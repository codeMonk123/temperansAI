from temperans.xyzabc323_dataset import build_xyzabc323
def test_xyzabc323_shape():
 a=build_xyzabc323()
 assert len(a)==75
 assert len({x["event_id"] for x in a})==75
 assert len({x["surface"] for x in a})>=3
def test_xyzabc323_has_heldout_edge_cases():
 a=build_xyzabc323()
 assert any(x["_gold_relation"]=="ambiguous_cross_person" for x in a)
 assert any(x["_gold_relation"]=="clarify" for x in a)
