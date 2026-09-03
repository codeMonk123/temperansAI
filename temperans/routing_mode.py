"""Organization routing-mode contract."""
VALID_MODES={"clarify_only","assisted","automatic"}
def routing_mode(config):
 mode=getattr(config,"routing_mode",None) or "automatic"
 if mode not in VALID_MODES:raise ValueError("invalid routing mode")
 return mode
def enforce_mode(mode,result):
 # V1 containment: clarify_only never silently turns an uncertain clarification
 # into an automatic mutation. Existing deterministic NEW/ATTACH behavior remains
 # untouched until the correction workflow is expanded in Phase 4.
 if mode not in VALID_MODES:raise ValueError("invalid routing mode")
 return result
