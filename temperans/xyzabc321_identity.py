"""Known identity setup for synthetic XYZABC321 only."""
SURFACES=("slack","generic_chatbot","mcp")
def link_xyzabc321_identities(runtime):
 for u in range(1,21):
  external=f"user_{u:02d}";person=f"xyz_person_{u:02d}"
  for surface in SURFACES:
   runtime.link_identity(workspace_id="production",surface=surface,
    external_user_id=external,person_id=person)
