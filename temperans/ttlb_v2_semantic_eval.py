import argparse,json
from pathlib import Path
from temperans.mock_semantic_judge import MockSemanticJudge
from temperans.semantic_cache import JsonSemanticCache
from temperans.semantic_recovery import SemanticRecoveryEngine
from temperans.workstate import ConversationState,TrajectoryState

def load(path): return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
def states(item,c):
    t=TrajectoryState(trajectory_id=c["candidate_id"],workspace_id="ttlb_v2",person_id="benchmark_user",durable_goal=c["goal"],current_state=c["state"],lifecycle=c["lifecycle"])
    conv=ConversationState(workspace_id="ttlb_v2",person_id="benchmark_user",conversation_id="incoming_"+item["case_id"],surface="benchmark",current_problem=item["incoming_text"])
    return t,conv

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--provider",choices=["mock","gemini"],default="mock"); ap.add_argument("--max-new",type=int,default=20); args=ap.parse_args()
    items=load("ttlb_v2_semantic_abstentions.jsonl")
    if args.provider=="mock": judge=MockSemanticJudge(); cachefile="ttlb_v2_semantic_mock_cache.jsonl"
    else:
        from google import genai
        from temperans.frontier_judge import GeminiFrontierJudge
        judge=GeminiFrontierJudge(client=genai.Client()); cachefile="ttlb_v2_semantic_gemini_cache.jsonl"
    cache=JsonSemanticCache(cachefile); engine=SemanticRecoveryEngine(judge,provider=args.provider,cache=cache)
    completed=0; correct=0; wrong_attach=0; uncertain=0
    for item in items:
        if completed>=args.max_new: break
        # Judge semantic top-1 only in V1; multi-candidate semantic comparison comes next.
        cand=item["ranked_candidates"][0]; t,c=states(item,cand)
        try: d=engine.recover(t,c,{"semantic_score":cand["semantic_score"]})
        except Exception as exc:
            print("INTERRUPTED:",type(exc).__name__,str(exc)[:300]); break
        completed+=1
        ok=(d.decision==item["expected_decision"] and (item["expected_candidate_id"] is None or d.candidate_id==item["expected_candidate_id"]))
        correct+=int(ok); uncertain+=int(d.decision=="uncertain")
        wrong_attach+=int(d.decision=="attach" and not ok)
        print(item["case_id"],"expected=",item["expected_decision"],"predicted=",d.decision,"confidence=",d.confidence,"provider=",d.provider)
    print("\nSEMANTIC RECOVERY STATUS")
    print("EVALUATED:",completed,"/",len(items)); print("CORRECT:",correct); print("UNCERTAIN:",uncertain); print("WRONG ATTACHES:",wrong_attach)
    if completed: print("ACCURACY:",round(correct/completed,4))
if __name__=="__main__": main()
