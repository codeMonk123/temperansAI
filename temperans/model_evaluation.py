"""Network-optional Kimi evaluation harness; never mutates trajectory state."""
from copy import deepcopy
def evaluate_provider(provider,request):
 before=deepcopy(request.candidate_views)
 result=provider.perceive(request)
 if request.candidate_views!=before:raise RuntimeError("perception provider mutated candidate views")
 for s in result.signals:
  if s.maturity!="L2":raise RuntimeError("model provider emitted non-L2 signal")
  if s.policy_eligible:raise RuntimeError("model L2 signal became policy eligible")
 return result
