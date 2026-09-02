import re
from dataclasses import dataclass

@dataclass
class RedactionResult:
    text:str
    redacted:bool
    categories:list

class Redactor:
    EMAIL=re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",re.I)
    PHONE=re.compile(r"(?<!\w)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\w)")
    IPV4=re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    def redact(self,text):
        text=text or ""; cats=[]
        for pattern,repl,cat in [(self.EMAIL,"[REDACTED_EMAIL]","email"),(self.PHONE,"[REDACTED_PHONE]","phone"),(self.IPV4,"[REDACTED_IP]","ip")]:
            text,n=pattern.subn(repl,text)
            if n: cats.append(cat)
        return RedactionResult(text,bool(cats),sorted(set(cats)))
