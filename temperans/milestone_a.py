"""Frozen Milestone A scoring contract."""
def score(*,trajectory_reconstruction_rate,false_merges,human_correct_rate=None,
          human_false_merges=None):
    machine=(trajectory_reconstruction_rate>=.70 and false_merges==0)
    human=(human_correct_rate is not None and human_false_merges is not None
           and human_correct_rate>=.70 and human_false_merges==0)
    return {"machine_gate":machine,"human_gate":human,
            "milestone_a_pass":machine and human}
