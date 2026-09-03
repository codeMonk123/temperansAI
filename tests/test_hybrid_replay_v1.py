from temperans.hybrid_replay_v1 import summarize
def test_summary_requires_entire_work_correct():
 rows=[
 {"gold_work":"a","final_action":"new","correct":True},
 {"gold_work":"a","final_action":"attach","correct":True},
 {"gold_work":"b","final_action":"new","correct":True},
 {"gold_work":"b","final_action":"clarify","correct":False}]
 s=summarize(rows)
 assert s["gold_trajectories"]==2
 assert s["correctly_reconstructed_trajectories"]==1
 assert s["trajectory_reconstruction_rate"]==.5
