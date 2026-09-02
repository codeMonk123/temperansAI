from temperans.frontier_judge import FrontierDecision
class MockSemanticJudge:
    def judge(self,trajectory,conversation,structural_evidence=None):
        old=(getattr(trajectory,"durable_goal","") or "").lower().strip()
        new=(getattr(conversation,"goal","") or "").lower().strip()
        incoming=(getattr(conversation,"current_problem","") or "").lower()
        lifecycle=(getattr(trajectory,"lifecycle","") or "").lower()
        if old and new and old==new:
            return FrontierDecision("attach",.95,["mock exact goal continuity"])
        if lifecycle=="resolved" and "same" in incoming and ("back" in incoming or "again" in incoming):
            return FrontierDecision("attach",.92,["mock explicit recurrence"])
        return FrontierDecision("uncertain",.50,["mock intentionally abstains"])
