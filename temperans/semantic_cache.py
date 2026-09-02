import json
from pathlib import Path
class JsonSemanticCache:
    def __init__(self,path):
        self.path=Path(path); self.items={}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item=json.loads(line); self.items[item["signature"]]=item
    def get(self,signature): return self.items.get(signature)
    def put(self,item):
        sig=item["signature"]
        if sig in self.items: return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open("a",encoding="utf-8") as f: f.write(json.dumps(item,ensure_ascii=False)+"\n")
        self.items[sig]=item
