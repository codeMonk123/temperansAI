#!/usr/bin/env python3
"""Deep XYZABC321 runtime probe. DEVELOPMENT SET ONLY. No behavior changes, no APIs."""
import json,tempfile
from pathlib import Path
from collections import Counter,defaultdict
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities

def clean(e):
    x=dict(e);x.pop("_gold_trajectory",None);return x

def text_of(runtime,obj):
    return runtime.service.runtime._text(obj)

with tempfile.TemporaryDirectory() as d:
    p=TemperansPlatform(d)
    p.create_organization(organization_id="XYZABC321",name="XYZABC321")
    rt=p.runtime("XYZABC321")
    link_xyzabc321_identities(rt)
    events,_=build_xyzabc321()
    R=rt.service.runtime
    rows=[]

    for e in events:
        # Build the same canonical/service state used by OrganizationRuntime,
        # but inspect candidates BEFORE authoritative observe mutates anything.
        ev=rt.adapter.normalize(organization_id="XYZABC321",payload=clean(e))
        person=rt.identities.resolve(ev.workspace_id,ev.surface,ev.external_user_id,True)
        work=rt.extractor.extract(text=ev.text,supplied_goal=ev.goal,
                                  entities=ev.entities,artifacts=ev.artifacts)
        from temperans.workstate import ConversationState
        c=ConversationState(workspace_id=ev.workspace_id,person_id=person,
            conversation_id=ev.conversation_id,surface=ev.surface,
            goal=work.goal,current_problem=work.current_problem,
            entities=work.entities,artifacts=work.artifacts,anchors=work.anchors)

        # Mirror current RuntimeV2 candidate retrieval, including P0-1 rescue.
        R._anchors(c)
        person_candidates=[t for t in R.trajectories.values()
            if t.workspace_id==c.workspace_id and t.person_id==c.person_id]
        rescue=[t for t in R.trajectories.values()
            if t.workspace_id==c.workspace_id and t.person_id!=c.person_id
            and R.anchor_recall.relevant(t,c)]
        seen=set();candidates=[]
        for t in person_candidates+rescue:
            if t.trajectory_id not in seen:
                candidates.append(t);seen.add(t.trajectory_id)

        detail=[]
        decisions=[]
        for t in candidates:
            score=float(R.semantic_scorer(t,c))
            lang=R.language.extract(candidate_text=text_of(rt,t),new_text=text_of(rt,c))
            ld=R.linker.decide(trajectory=t,conversation=c,semantic_score=score,
                branch_signal=lang.has_branch_signal,
                continuation_signal=lang.has_continuation_signal)
            decisions.append((score,t,ld))
            detail.append({"trajectory_id":t.trajectory_id,
                "cross_person":t in rescue,
                "semantic_score":score,
                "anchor_relevant":bool(R.anchor_recall.relevant(t,c)),
                "continuation_signal":bool(lang.has_continuation_signal),
                "branch_signal":bool(lang.has_branch_signal),
                "linker_decision":ld.decision,
                "linker_confidence":getattr(ld,"confidence",None),
                "linker_reasons":getattr(ld,"reasons",None)})

        set_decision=None;gate_decision=None
        if decisions:
            from temperans.runtime_v2 import Candidate
            packed=[(s,Candidate(t),ld) for s,t,ld in decisions]
            sr=R.set_resolver.resolve(packed)
            set_decision={"decision":sr.decision,"confidence":sr.confidence}
            if any(ld.decision in {"attach","branch"} for _,_,ld in decisions):
                g=R.gate.choose(packed)
                gate_decision={"decision":g.decision,
                    "candidate_id":g.candidate_id,"confidence":g.confidence,
                    "reasons":g.reasons}

        result=rt.observe(clean(e))
        if result["decision"]=="clarify":
            ranked=sorted(detail,key=lambda x:x["semantic_score"],reverse=True)
            rows.append({"event_id":e["event_id"],"gold_work":e["_gold_trajectory"],
                "candidate_count":len(detail),"person_candidate_count":len(person_candidates),
                "rescue_candidate_count":len(rescue),"candidates":ranked,
                "set_resolver":set_decision,"candidate_gate":gate_decision,
                "result_source":result.get("source")})

    linker=Counter()
    anchors=Counter()
    candidate_counts=Counter()
    set_results=Counter()
    gate_results=Counter()
    top_bands=Counter()
    def band(x):
        if x is None:return "none"
        if x<.12:return "<.12"
        if x<.30:return ".12-.30"
        if x<.50:return ".30-.50"
        if x<.70:return ".50-.70"
        return ">=.70"
    for r in rows:
        candidate_counts[str(r["candidate_count"])]+=1
        set_results[(r["set_resolver"] or {}).get("decision","none")]+=1
        gate_results[(r["candidate_gate"] or {}).get("decision","none")]+=1
        top=r["candidates"][0] if r["candidates"] else None
        top_bands[band(top["semantic_score"] if top else None)]+=1
        anchors["top_anchor_relevant" if top and top["anchor_relevant"] else "top_anchor_not_relevant"]+=1
        for c in r["candidates"]:linker[c["linker_decision"]]+=1

    summary={"clarifications":len(rows),
        "candidate_count_distribution":dict(candidate_counts),
        "top_score_bands":dict(top_bands),
        "top_anchor":dict(anchors),
        "linker_decisions_all_candidates":dict(linker),
        "set_resolver_decisions":dict(set_results),
        "candidate_gate_decisions":dict(gate_results)}
    Path("xyzabc321_runtime_deep_diagnostic.json").write_text(
        json.dumps({"summary":summary,"rows":rows},indent=2,default=str))
    print(json.dumps(summary,indent=2,default=str))
