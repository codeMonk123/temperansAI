class AnchorCandidateRecall:
    STRONG={"ticket","incident","pr","trace_id","slack_thread","email_thread"}
    BOUNDARY={"customer","tenant","account"}
    @staticmethod
    def idx(xs):
        d={}
        for x in xs or []: d.setdefault(x.type,set()).add(x.value.lower())
        return d
    def relevant(self,t,c):
        a,b=self.idx(t.anchors),self.idx(c.anchors)
        return any(a.get(k,set()) & b.get(k,set()) for k in self.STRONG) or any(a.get(k) and b.get(k) for k in self.BOUNDARY)
