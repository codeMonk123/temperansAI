from temperans.platform import TemperansPlatform
from temperans.organization import OrganizationConfig

def payload(e="e"):
 return {"event_id":e,"workspace_id":"w","external_user_id":"u","surface":"chat",
 "conversation_id":"c","content":{"text":"Ticket PROD-218 failed"}}

def test_default_runtime_mode_remains_automatic(tmp_path):
 p=TemperansPlatform(tmp_path/"p");c=p.create_organization(organization_id="o",name="o")
 r=p.observe_with_key(api_key=c["api_key"],payload=payload())
 assert r["routing_mode"]=="automatic"
 assert r["requires_confirmation"] is False

def test_clarify_only_is_available_on_runtime_config(tmp_path):
 p=TemperansPlatform(tmp_path/"p");c=p.create_organization(organization_id="o",name="o")
 rt=p.runtime("o")
 # V1 runtime mode can be enabled explicitly without changing persisted org schema.
 rt.config.routing_mode="clarify_only"
 r=p.observe_with_key(api_key=c["api_key"],payload=payload())
 assert r["routing_mode"]=="clarify_only"
 assert r["decision"]=="clarify"
 assert r["requires_confirmation"] is True
 assert r["proposed_decision"] in {"new","attach","branch"}

def test_signals_and_instrumentation_survive_runtime_control(tmp_path):
 p=TemperansPlatform(tmp_path/"p");c=p.create_organization(organization_id="o",name="o")
 r=p.observe_with_key(api_key=c["api_key"],payload=payload())
 assert r["signals"]
 assert r["instrumentation"]["instrumentation_version"]=="runtime-instrumentation-v1"
