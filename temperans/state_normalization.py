from copy import deepcopy
NORMALIZATION_VERSION="trajectory-normalization-v1"
KEEP_FIELDS=("durable_goal","current_state","lifecycle","entities","artifacts","anchors","open_questions","resolved_questions","decisions","attempts","failures","outcomes","surfaces","conversation_ids","recent_context")
SET_FIELDS={"entities","artifacts","anchors","open_questions","resolved_questions","decisions","attempts","failures","outcomes","surfaces","conversation_ids"}
def _norm(field,value):
    value=deepcopy(value)
    if field=="anchors":
        rows=[]
        for a in value or []:
            if hasattr(a,"to_dict"): a=a.to_dict()
            rows.append(a)
        return sorted(rows,key=lambda x:repr(x))
    if field in SET_FIELDS:return sorted(value or [],key=lambda x:repr(x))
    return value
def normalized_trajectory_state(value):
    if hasattr(value,"to_dict"):value=value.to_dict()
    value=value or {}
    return {f:_norm(f,value.get(f)) for f in KEEP_FIELDS}
def normalized_trajectory_set(values):
    if isinstance(values,dict):values=list(values.values())
    return sorted([normalized_trajectory_state(v) for v in values or []],key=repr)
def compare_normalized(left,right):
    a,b=normalized_trajectory_set(left),normalized_trajectory_set(right)
    if a==b:return {"equivalent":True,"normalization_version":NORMALIZATION_VERSION,"differences":[]}
    diffs=[]
    for i in range(max(len(a),len(b))):
        x=a[i] if i<len(a) else {}; y=b[i] if i<len(b) else {}
        for f in sorted(set(x)|set(y)):
            if x.get(f)!=y.get(f):diffs.append({"trajectory_index":i,"field":f,"left":x.get(f),"right":y.get(f)})
    return {"equivalent":False,"normalization_version":NORMALIZATION_VERSION,"differences":diffs}
