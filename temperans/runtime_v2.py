from dataclasses import dataclass, asdict
import uuid

from temperans.anchors import AnchorExtractor
from temperans.anchor_retrieval import AnchorCandidateRecall
from temperans.candidate_gate import CandidateDecisionGate
from temperans.candidate_set import CandidateSetResolver
from temperans.context_pack import ContextPackBuilder
from temperans.decision_trace import DecisionRule, DecisionTrace, deterministic_signature
from temperans.linkage import LinkageEvidenceExtractor
from temperans.no_match_gate import NoMatchGate
from temperans.reopen_gate import ReopenGate
from temperans.structured_linker import StructuredTrajectoryLinker, UNCERTAIN
from temperans.workstate import TrajectoryState


@dataclass
class RuntimeDecision:
    decision: str
    trajectory_id: str | None
    confidence: float
    source: str
    context_pack: dict | None
    trace: dict

    def to_dict(self):
        return asdict(self)


class Candidate:
    def __init__(self, trajectory):
        self.trajectory = trajectory
        self.candidate_id = trajectory.trajectory_id
        self.lifecycle = trajectory.lifecycle


class TemperansRuntimeV2:
    def __init__(self, semantic_scorer, frontier_judge=None, candidate_floor=0.12):
        self.semantic_scorer = semantic_scorer
        self.frontier_judge = frontier_judge
        self.candidate_floor = candidate_floor
        self.trajectories = {}
        self.extractor = AnchorExtractor()
        self.anchor_recall = AnchorCandidateRecall()
        self.language = LinkageEvidenceExtractor()
        self.linker = StructuredTrajectoryLinker()
        self.set_resolver = CandidateSetResolver()
        self.gate = CandidateDecisionGate()
        self.reopen = ReopenGate(min_score=0.25, min_margin=0.15)
        self.no_match = NoMatchGate(max_no_match_score=0.12)
        self.context = ContextPackBuilder()

    def _text(self, x):
        vals = [
            getattr(x, "durable_goal", getattr(x, "goal", "")),
            getattr(x, "current_state", getattr(x, "current_problem", "")),
            *getattr(x, "entities", []),
            *getattr(x, "artifacts", []),
        ]
        return " ".join(str(v) for v in vals if v)

    def _anchors(self, state):
        found = self.extractor.extract(self._text(state))
        existing = {(a.type, a.value.lower()) for a in state.anchors}
        for a in found:
            if (a.type, a.value.lower()) not in existing:
                state.anchors.append(a)
                existing.add((a.type, a.value.lower()))

    def _new(self, c):
        t = TrajectoryState(
            trajectory_id="traj_" + uuid.uuid4().hex[:12],
            workspace_id=c.workspace_id,
            person_id=c.person_id,
            durable_goal=c.goal,
            current_state=c.current_problem,
            lifecycle="active",
        )
        t.apply(c)
        self._anchors(t)
        self.trajectories[t.trajectory_id] = t
        return t

    def _result(self, decision, t, confidence, source, rules, top=None, second=None):
        sig = deterministic_signature({
            "decision": decision,
            "trajectory_id": t.trajectory_id if t else None,
            "state": self._text(t) if t else "",
        })
        trace = DecisionTrace(
            decision=decision,
            source=source,
            confidence=confidence,
            trajectory_id=t.trajectory_id if t else None,
            candidate_score=top,
            second_score=second,
            margin=(top-second) if top is not None and second is not None else None,
            abstained=(decision == "clarify"),
            frontier_used=source.startswith("frontier_judge"),
            rules=rules,
            input_signature=sig,
        ).to_dict()
        return RuntimeDecision(
            decision=decision,
            trajectory_id=t.trajectory_id if t else None,
            confidence=confidence,
            source=source,
            context_pack=self.context.build(t).to_dict() if t else None,
            trace=trace,
        )

    def process(self, c):
        self._anchors(c)
        person_candidates = [
            t for t in self.trajectories.values()
            if t.workspace_id == c.workspace_id and t.person_id == c.person_id
        ]
        rescue_candidates = [
            t for t in self.trajectories.values()
            if t.workspace_id == c.workspace_id
            and t.person_id != c.person_id
            and self.anchor_recall.relevant(t, c)
        ]
        seen = set()
        candidates = []
        for t in person_candidates + rescue_candidates:
            if t.trajectory_id not in seen:
                candidates.append(t)
                seen.add(t.trajectory_id)
        cross_person_ids = {t.trajectory_id for t in rescue_candidates}

        if not candidates:
            t = self._new(c)
            return self._result(
                "new", t, 1.0, "no_candidates",
                [DecisionRule(rule="no_candidates", effect="new",
                              explanation="no existing trajectories")]
            )

        ranked = sorted(
            [(float(self.semantic_scorer(t, c)), t) for t in candidates],
            key=lambda x: x[0], reverse=True
        )
        top = ranked[0][0]
        second = ranked[1][0] if len(ranked) > 1 else None

        structural_recall = any(self.anchor_recall.relevant(t, c) for _, t in ranked)
        if top < self.candidate_floor and not structural_recall:
            t = self._new(c)
            return self._result(
                "new", t, .90, "candidate_retrieval",
                [DecisionRule(rule="candidate_floor", effect="new",
                              evidence={"top": top, "floor": self.candidate_floor},
                              explanation="no plausible candidate")],
                top, second
            )

        decisions = []
        for score, t in ranked:
            lang = self.language.extract(
                candidate_text=self._text(t),
                new_text=self._text(c),
            )
            d = self.linker.decide(
                trajectory=t,
                conversation=c,
                semantic_score=score,
                branch_signal=lang.has_branch_signal,
                continuation_signal=lang.has_continuation_signal,
            )
            decisions.append((score, Candidate(t), d))

        set_result = self.set_resolver.resolve(decisions)
        action, chosen, confidence, source = UNCERTAIN, None, .50, "temperans_local"
        rules = []

        if set_result.decision == "new":
            action, confidence = "new", set_result.confidence
        elif any(d.decision in {"attach", "branch"} for _, _, d in decisions):
            g = self.gate.choose(decisions)
            action, chosen, confidence = g.decision, g.candidate_id, g.confidence
            rules.append(DecisionRule(
                rule="candidate_gate", effect=action,
                explanation="; ".join(g.reasons)
            ))

        if action == UNCERTAIN:
            r = self.reopen.choose(
                ranked_candidates=[(s, cnd) for s, cnd, _ in decisions],
                incoming_text=self._text(c),
            )
            if r.decision == "attach":
                action, chosen, confidence, source = "attach", r.candidate_id, r.confidence, "reopen_gate"

        if action == UNCERTAIN:
            n = self.no_match.choose(decisions=decisions)
            if n.decision == "new":
                action, confidence, source = "new", n.confidence, "no_match_gate"

        if action == UNCERTAIN:
            t = ranked[0][1]
            return self._result(
                "clarify", t, confidence, "user_clarification",
                rules + [DecisionRule(rule="abstain", effect="clarify",
                                      explanation="insufficient evidence for safe routing")],
                top, second
            )

        if action == "new":
            t = self._new(c)
            return self._result("new", t, confidence, source, rules, top, second)

        t = self.trajectories.get(chosen)
        if t is None:
            return self._result(
                "clarify", ranked[0][1], .40, "user_clarification",
                [DecisionRule(rule="missing_candidate", effect="clarify",
                              explanation="chosen candidate missing")],
                top, second
            )

        if action in {"attach", "branch"} and t.trajectory_id in cross_person_ids:
            return self._result(
                "clarify", t, confidence, "cross_person_structural_rescue",
                rules + [DecisionRule(
                    rule="cross_person_anchor_rescue",
                    effect="clarify",
                    evidence={"candidate_id": t.trajectory_id},
                    explanation="strong work anchor widened retrieval across person identity; identity remains unlinked"
                )],
                top, second
            )

        if action == "attach":
            t.apply(c)
            self._anchors(t)
            return self._result("attach", t, confidence, source, rules, top, second)

        if action == "branch":
            parent = t
            child = self._new(c)
            child.recent_context.insert(0, "branched from " + parent.trajectory_id)
            return self._result("branch", child, confidence, source, rules, top, second)

        raise RuntimeError(action)
