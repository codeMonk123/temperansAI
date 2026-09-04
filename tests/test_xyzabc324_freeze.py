from temperans.xyzabc324_dataset import build_xyzabc324
def test_xyzabc324_frozen_shape():
 x=build_xyzabc324();assert len(x)==85 and len({r["event_id"] for r in x})==85
 assert len({r["surface"] for r in x})>=3
 assert any(r["_gold_relation"]=="ambiguous_cross_person" for r in x)
 assert any(r["_gold_relation"]=="clarify" for r in x)
