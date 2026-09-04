"""XYZABC321 development-only semantic recovery experiment.
Does not mutate production routing and does not touch XYZABC324.
"""
import json,os,tempfile
from collections import Counter
from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.kimi_frontier_assessor_v2 import KimiFrontierAssessor
from temperans.gemini_frontier_assessor import GeminiFrontierAssessor
from temperans.semantic_recovery_service import SemanticRecoveryService
from temperans.workstate import ConversationState

def clean(e):
    x=dict(e);x.pop("_gold_trajectory",None);return x

k=os.environ.get("MOONSHOT_API_KEY");g=os.environ.get("GEMINI_API_KEY")
if not k or not g: raise SystemExit("Both MOONSHOT_API_KEY and GEMINI_API_KEY required for anchorless consensus")
svc=SemanticRecoveryService(
    KimiFrontierAssessor(k,os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k3")),
    GeminiFrontierAssessor(g,os.environ.get("TEMPERANS_GEMINI_MODEL","gemini-3.6-flash")))
limit=int(os.environ.get("TEMPERANS_RECOVERY_MAX_CALLS","10"))
attempted=accepted=0;reasons=Counter()

with tempfile.TemporaryDirectory() as d:
    p=TemperansPlatform(d);p.create_organization(organization_id="XYZABC321",name="XYZABC321")
    rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt);events,_=build_xyzabc321();R=rt.service.runtime
    for e in events:
        ev=rt.adapter.normalize(organization_id="XYZABC321",payload=clean(e))
        person=rt.identities.resolve(ev.workspace_id,ev.surface,ev.external_user_id,True)
        work=rt.extractor.extract(text=ev.text,supplied_goal=ev.goal,entities=ev.entities,artifacts=ev.artifacts)
        c=ConversationState(workspace_id=ev.workspace_id,person_id=person,conversation_id=ev.conversation_id,
            surface=ev.surface,goal=work.goal,current_problem=work.current_problem,
            entities=work.entities,artifacts=work.artifacts,anchors=work.anchors)
        R._anchors(c)
        candidates=[t for t in R.trajectories.values() if t.workspace_id==c.workspace_id and t.person_id==c.person_id]
        result=rt.observe(clean(e))
        if result["decision"]!="clarify" or len(candidates)!=1 or attempted>=limit: continue
        t=candidates[0];score=float(R.semantic_scorer(t,c))
        lang=R.language.extract(candidate_text=R._text(t),new_text=R._text(c))
        ld=R.linker.decide(trajectory=t,conversation=c,semantic_score=score,
            branch_signal=lang.has_branch_signal,continuation_signal=lang.has_continuation_signal)
        anchor=bool(R.anchor_recall.relevant(t,c))
        view=t.to_dict();view["anchors"]=[a.to_dict() for a in t.anchors]
        attempted+=1
        print(f"Recovery {attempted}/{limit}: {e['event_id']}",flush=True)
        try:
            x=svc.assess(event=clean(e),candidate_views=[view],deterministic_result=result,
                top_anchor_relevant=anchor,linker_decision=ld.decision)
        except Exception as ex:
            x={"decision":"clarify","accepted":False,"reason":"provider_error:"+type(ex).__name__}
        accepted+=int(x.get("accepted",False));reasons[x.get("reason","unknown")]+=1
    report={"development_set":"XYZABC321","attempted":attempted,"accepted":accepted,
        "accept_rate":accepted/attempted if attempted else 0,"reasons":dict(reasons),
        "note":"Development experiment only; no XYZABC324 access and no authoritative recovery mutation."}
    print(json.dumps(report,indent=2))
