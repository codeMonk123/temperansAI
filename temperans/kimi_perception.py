"""Optional Moonshot/Kimi L2 perception provider.

Correctness never depends on this provider. It emits L2 perceptions only.
Uses stdlib urllib so Temperans gains no new runtime dependency.
"""
import json, os
from urllib.request import Request, urlopen

from temperans.perception_provider import PerceptionProvider,PerceptionResult
from temperans.signals import SignalObservation

class KimiPerceptionProvider(PerceptionProvider):
    ADAPTER_VERSION="kimi-perception-v1"
    ALLOWED={"resistance","frustration","goal_shift","progress","regression",
             "repair","refinement","disagreement","context_loss"}

    def __init__(self,api_key=None,model=None,base_url=None,
                 taxonomy_version="1.0.0",taxonomy_sha256=""):
        self.api_key=api_key or os.environ.get("MOONSHOT_API_KEY")
        self.model=model or os.environ.get("TEMPERANS_KIMI_MODEL","kimi-k2.5")
        self.base_url=(base_url or os.environ.get(
            "TEMPERANS_KIMI_BASE_URL","https://api.moonshot.ai/v1")).rstrip("/")
        self.taxonomy_version=taxonomy_version
        self.taxonomy_sha256=taxonomy_sha256

    def _prompt(self,request):
        return (
          "Return JSON only: {signals:[{name,value,confidence,evidence}]}. "
          "Allowed signal names: "+",".join(sorted(self.ALLOWED))+
          ". Values must be numbers 0..1. These are perceptions, not facts.\n"+
          json.dumps({"event":request.event,"candidate_views":request.candidate_views},
                     ensure_ascii=False,sort_keys=True)
        )

    def perceive(self,request):
        if not self.api_key:raise RuntimeError("MOONSHOT_API_KEY is required")
        body={"model":self.model,"messages":[
            {"role":"system","content":"You are a trajectory perception component. Output strict JSON only."},
            {"role":"user","content":self._prompt(request)}],
            "temperature":0}
        req=Request(self.base_url+"/chat/completions",
            data=json.dumps(body).encode(),method="POST",
            headers={"Authorization":"Bearer "+self.api_key,"Content-Type":"application/json"})
        with urlopen(req,timeout=60) as r:raw=json.loads(r.read())
        content=raw["choices"][0]["message"]["content"]
        parsed=json.loads(content)
        signals=[]
        for x in parsed.get("signals",[]):
            name=x.get("name")
            if name not in self.ALLOWED:continue
            value=float(x.get("value",0))
            if not 0<=value<=1:continue
            signals.append(SignalObservation(
                signal="temperans."+name,value=value,maturity="L2",
                taxonomy_version=self.taxonomy_version,
                taxonomy_sha256=self.taxonomy_sha256,
                producer_version=self.ADAPTER_VERSION,
                provenance=["canonical_event","trajectory_context","model_inference"],
                evidence=list(x.get("evidence",[])),
                confidence=float(x["confidence"]) if x.get("confidence") is not None else None))
        return PerceptionResult(provider="moonshot",model=self.model,
            adapter_version=self.ADAPTER_VERSION,signals=signals,
            raw_metadata={"usage":raw.get("usage",{})})
