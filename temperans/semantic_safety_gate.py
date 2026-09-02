from dataclasses import dataclass, field
from temperans.anchor_evidence import AnchorEvidenceEngine
from temperans.lifecycle import LifecycleEvidenceEngine

@dataclass
class SafetyDecision:
    decision: str
    accepted: bool
    candidate_id: str | None
    confidence: float
    reasons: list[str] = field(default_factory=list)

class SemanticSafetyGate:
    def __init__(self, min_conf=.80, min_score=.20, min_margin=.12):
        self.min_conf=min_conf; self.min_score=min_score; self.min_margin=min_margin
        self.anchors=AnchorEvidenceEngine(); self.lifecycle=LifecycleEvidenceEngine()

    def validate(self, frontier_decision, frontier_confidence, candidate,
                 conversation, candidate_score, second_score=None,
                 is_top_candidate=True):
        d=(frontier_decision or "").lower().strip()
        cid=getattr(candidate,"trajectory_id",None)
        if d not in {"attach","branch","new","uncertain"} or frontier_confidence < self.min_conf or d=="uncertain":
            return SafetyDecision("uncertain",False,cid,frontier_confidence,["frontier judgment insufficient"])

        ae=self.anchors.compare(getattr(candidate,"anchors",[]),getattr(conversation,"anchors",[]))
        if ae.hard_new:
            if d=="new":
                return SafetyDecision("new",True,None,frontier_confidence,["NEW agrees with identity boundary"])
            return SafetyDecision("uncertain",False,cid,frontier_confidence,["positive frontier decision conflicts with identity boundary"])

        if ae.strong_attach:
            if d=="attach":
                return SafetyDecision("attach",True,cid,frontier_confidence,["ATTACH confirmed by strong trajectory anchor"])
            if d=="new":
                return SafetyDecision("uncertain",False,cid,frontier_confidence,["NEW conflicts with strong trajectory anchor"])

        old_goal=" ".join((getattr(candidate,"durable_goal","") or "").lower().split())
        new_goal=" ".join((getattr(conversation,"goal","") or "").lower().split())
        exact_goal=bool(old_goal and new_goal and old_goal==new_goal)
        margin=candidate_score-(second_score if second_score is not None else 0.0)
        reopen=self.lifecycle.extract(
            lifecycle=getattr(candidate,"lifecycle",""),
            incoming_text=getattr(conversation,"current_problem","")
        ).reopen_signal

        if d=="attach":
            if not is_top_candidate:
                return SafetyDecision("uncertain",False,cid,frontier_confidence,["ATTACH is not semantic top candidate"])
            if exact_goal:
                return SafetyDecision("attach",True,cid,frontier_confidence,["exact durable-goal continuity"])
            if reopen and candidate_score>=self.min_score and margin>=self.min_margin:
                return SafetyDecision("attach",True,cid,frontier_confidence,["resolved recurrence with sufficient separation"])
            if candidate_score>=self.min_score and margin>=self.min_margin and not ae.scope_matches:
                return SafetyDecision("attach",True,cid,frontier_confidence,["well-separated top candidate without scope-only identity"])
            return SafetyDecision("uncertain",False,cid,frontier_confidence,["ATTACH lacks trajectory-specific evidence"])

        if d=="branch":
            if is_top_candidate and candidate_score>=self.min_score:
                return SafetyDecision("branch",True,cid,frontier_confidence,["plausible branch parent"])
            return SafetyDecision("uncertain",False,cid,frontier_confidence,["BRANCH parent insufficiently plausible"])

        if d=="new":
            return SafetyDecision("new",True,None,frontier_confidence,["NEW has no contradictory strong anchor"])

        return SafetyDecision("uncertain",False,cid,frontier_confidence,["unresolved"])
