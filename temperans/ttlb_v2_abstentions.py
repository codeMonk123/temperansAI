import json
from temperans.anchors import AnchorExtractor
from temperans.candidate_gate import CandidateDecisionGate
from temperans.candidate_set import CandidateSetResolver
from temperans.linkage import LinkageEvidenceExtractor
from temperans.no_match_gate import NoMatchGate
from temperans.reopen_gate import ReopenGate
from temperans.structured_linker import StructuredTrajectoryLinker, UNCERTAIN
from temperans.ttlb_v2 import build_v2
from temperans.workstate import ConversationState, TrajectoryState

def ctext(c): return " ".join(x for x in [c.goal,c.state,c.text] if x)

def build_abstentions():
    cases=build_v2()
    rows=json.load(open("ttlb_v2_semantic_scores.json",encoding="utf-8"))
    scores={(r["case_id"],r["candidate_id"]):float(r["semantic_score"]) for r in rows}
    ex=AnchorExtractor(); lang=LinkageEvidenceExtractor(); linker=StructuredTrajectoryLinker(); cs=CandidateSetResolver(); gate=CandidateDecisionGate(); reopen=ReopenGate(.25,.15); no=NoMatchGate(.12)
    out=[]
    for case in cases:
        ranked=sorted([(scores[(case.case_id,c.candidate_id)],c) for c in case.candidates],key=lambda x:x[0],reverse=True)
        decisions=[]
        for score,c in ranked:
            old=ctext(c)
            t=TrajectoryState(trajectory_id=c.candidate_id,workspace_id="ttlb_v2",person_id="benchmark_user",durable_goal=c.goal,current_state=c.state,lifecycle=c.lifecycle,anchors=ex.extract(old))
            conv=ConversationState(workspace_id="ttlb_v2",person_id="benchmark_user",conversation_id="incoming_"+case.case_id,surface="benchmark",current_problem=case.incoming_text,anchors=ex.extract(case.incoming_text))
            le=lang.extract(candidate_text=old,new_text=case.incoming_text)
            d=linker.decide(trajectory=t,conversation=conv,semantic_score=score,branch_signal=le.has_branch_signal,continuation_signal=le.has_continuation_signal)
            decisions.append((score,c,d))
        sr=cs.resolve(decisions); local=UNCERTAIN
        if sr.decision=="new": local="new"
        elif any(d.decision in {"attach","branch"} for _,_,d in decisions): local=gate.choose(decisions).decision
        if local==UNCERTAIN:
            rr=reopen.choose(ranked_candidates=ranked,incoming_text=case.incoming_text)
            if rr.decision=="attach": local="attach"
        if local==UNCERTAIN:
            nr=no.choose(decisions=decisions)
            if nr.decision=="new": local="new"
        if local==UNCERTAIN:
            out.append({"case_id":case.case_id,"category":case.category,"expected_decision":case.expected_decision,"expected_candidate_id":case.expected_candidate_id,"incoming_text":case.incoming_text,"ranked_candidates":[{"candidate_id":c.candidate_id,"semantic_score":s,"goal":c.goal,"state":c.state,"lifecycle":c.lifecycle,"text":c.text} for s,c in ranked]})
    return out

def main():
    out=build_abstentions(); path="ttlb_v2_semantic_abstentions.jsonl"
    with open(path,"w",encoding="utf-8") as f:
        for x in out: f.write(json.dumps(x,ensure_ascii=False)+"\n")
    print("DETERMINISTIC ABSTENTIONS:",len(out)); print("SAVED:",path)
if __name__=="__main__": main()
