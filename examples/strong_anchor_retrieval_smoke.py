from temperans.runtime_v2 import TemperansRuntimeV2
from temperans.workstate import ConversationState
r=TemperansRuntimeV2(semantic_scorer=lambda t,c:.01,candidate_floor=.12)
a=r.process(ConversationState(workspace_id='w',person_id='u',conversation_id='c1',surface='x',goal='deployment',current_problem='Ticket PROD-218 deployment fails'))
b=r.process(ConversationState(workspace_id='w',person_id='u',conversation_id='c2',surface='y',goal='',current_problem='Different wording update PROD-218'))
assert a.trajectory_id==b.trajectory_id and b.decision=='attach',(a,b)
print('STRONG ANCHOR RETRIEVAL: PASS')
