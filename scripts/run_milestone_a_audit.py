#!/usr/bin/env python3
import argparse,json
from temperans.milestone_a import score
p=argparse.ArgumentParser()
p.add_argument("--reconstruction",type=float,required=True)
p.add_argument("--false-merges",type=int,required=True)
p.add_argument("--human-correct",type=float,required=True)
p.add_argument("--human-false-merges",type=int,required=True)
a=p.parse_args()
print(json.dumps(score(trajectory_reconstruction_rate=a.reconstruction,false_merges=a.false_merges,
 human_correct_rate=a.human_correct,human_false_merges=a.human_false_merges),indent=2))
