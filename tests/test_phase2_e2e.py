from temperans.platform import TemperansPlatform
from temperans.phase2_equivalence import assert_three_path_equivalence
def runtime(root):
 p=TemperansPlatform(root);p.create_organization(organization_id="o",name="o");return p.runtime("o")
def events():
 return [{"event_id":"e1","workspace_id":"w","external_user_id":"u","surface":"slack","conversation_id":"c1","occurred_at":"2026-09-01T10:00:00+00:00","source_sequence":"1","content":{"text":"Ticket PROD-218 deployment is failing"}},{"event_id":"e2","workspace_id":"w","external_user_id":"u","surface":"chat","conversation_id":"c2","occurred_at":"2026-09-01T10:05:00+00:00","source_sequence":"2","content":{"text":"PROD-218 certificate mismatch after restart"}}]
def test_actual_live_import_replay_equivalence(tmp_path):
 assert assert_three_path_equivalence(runtime(tmp_path/"l"),runtime(tmp_path/"i"),runtime(tmp_path/"r"),events()).equivalent
def test_late_event_flags_without_rewriting_history(tmp_path):
 p=TemperansPlatform(tmp_path/"late");c=p.create_organization(organization_id="o",name="o");k=c["api_key"]
 base={"workspace_id":"w","external_user_id":"u","surface":"chat","conversation_id":"c"}
 newer=p.observe_with_key(api_key=k,payload={**base,"event_id":"new","occurred_at":"2026-09-01T11:00:00+00:00","content":{"text":"Ticket PROD-218 newer"}})
 older=p.observe_with_key(api_key=k,payload={**base,"event_id":"old","occurred_at":"2026-09-01T10:00:00+00:00","content":{"text":"Ticket PROD-218 older"}})
 assert older["late_event"] and older["history_disordered"] and older["recompute_recommended"]
 rt=p.runtime("o");assert rt.sqlite.get_event(organization_id="o",event_id="old")["late_event"]
 assert rt.sqlite.get_event(organization_id="o",event_id="new")["result"]==newer
