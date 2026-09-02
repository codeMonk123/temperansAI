from dataclasses import dataclass, asdict, field
import hashlib, json

@dataclass
class NormalizedWorkState:
    goal: str = ""
    current_problem: str = ""
    lifecycle: str = ""
    intent: str = ""
    entities: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)
    open_questions: list = field(default_factory=list)
    recent_context: list = field(default_factory=list)
    def to_dict(self): return asdict(self)
    def signature(self):
        raw=json.dumps(self.to_dict(),sort_keys=True,separators=(",",":"),ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

class WorkStateNormalizer:
    @staticmethod
    def _clean(v): return "" if v is None else " ".join(str(v).strip().split())
    @classmethod
    def _list(cls, values):
        out=[]; seen=set()
        for v in values or []:
            x=cls._clean(v); k=x.lower()
            if x and k not in seen: seen.add(k); out.append(x)
        return out
    def conversation(self,s):
        return NormalizedWorkState(
            goal=self._clean(getattr(s,"goal","")),
            current_problem=self._clean(getattr(s,"current_problem","")),
            intent=self._clean(getattr(s,"intent","")),
            entities=self._list(getattr(s,"entities",[])),
            artifacts=self._list(getattr(s,"artifacts",[])),
            open_questions=self._list(getattr(s,"unresolved",[])),
        )
    def trajectory(self,s):
        return NormalizedWorkState(
            goal=self._clean(getattr(s,"durable_goal","")),
            current_problem=self._clean(getattr(s,"current_state","")),
            lifecycle=self._clean(getattr(s,"lifecycle","")),
            entities=self._list(getattr(s,"entities",[])),
            artifacts=self._list(getattr(s,"artifacts",[])),
            open_questions=self._list(getattr(s,"open_questions",[])),
            recent_context=self._list(getattr(s,"recent_context",[])[-6:]),
        )
