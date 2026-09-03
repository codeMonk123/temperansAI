from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.gold_frontier import build_gold_frontier
def test_gold_frontier_is_balanced_and_exact():
 events,_=build_xyzabc321();cases=build_gold_frontier(events,max_users=1)
 assert len(cases)==6
 assert sum(c["kind"]=="new" for c in cases)==3
 assert sum(c["kind"]=="attach" for c in cases)==3
 for c in cases:
  ids={x["trajectory_id"] for x in c["candidate_views"]}
  if c["kind"]=="new":assert c["gold_candidate_id"] is None
  else:assert c["gold_candidate_id"] in ids
def test_attach_has_target_and_distractors():
 events,_=build_xyzabc321();cases=build_gold_frontier(events,max_users=1)
 for c in cases:
  if c["kind"]=="attach":assert len(c["candidate_views"])==3
