import json
import pytest
from temperans.event_adapter import GenericChatbotAdapter
from temperans.canonical_event import CanonicalEvent
from temperans.kimi_perception import KimiPerceptionProvider
from temperans.perception_provider import PerceptionRequest

def test_adapter_legacy_and_canonical_shapes():
 a=GenericChatbotAdapter()
 legacy=a.normalize(organization_id="o",payload={"event_id":"e","external_user_id":"u","conversation_id":"c","message":"hello"})
 modern=a.normalize(organization_id="o",payload={"event_id":"e2","external_user_id":"u","conversation_id":"c","content":{"text":"hello"},"metadata":{"x":1}})
 assert legacy.text=="hello" and modern.text=="hello"
 assert modern.metadata["x"]==1

def test_canonical_content_must_be_object():
 with pytest.raises(ValueError):
  GenericChatbotAdapter().normalize(organization_id="o",payload={"event_id":"e","external_user_id":"u","conversation_id":"c","content":"bad"})

def test_kimi_missing_key_is_explicit():
 p=KimiPerceptionProvider(api_key="")
 p.api_key=None
 with pytest.raises(RuntimeError):p.perceive(PerceptionRequest(event={}))

def test_kimi_is_l2_by_contract(monkeypatch):
 # Network-free shape test: allowed outputs are constrained by provider constants.
 assert "goal_shift" in KimiPerceptionProvider.ALLOWED
 assert "trajectory_created" not in KimiPerceptionProvider.ALLOWED
