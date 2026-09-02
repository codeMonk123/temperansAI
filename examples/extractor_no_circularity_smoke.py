from temperans.workstate_extractor_v1 import WorkStateExtractor
x=WorkStateExtractor().extract(text='Completely unrelated hiring discussion',supplied_goal='',trajectory_context=[{'goal':'restore production deployment'}])
assert x.goal!='restore production deployment',x
print('EXTRACTOR NO CIRCULARITY: PASS')
