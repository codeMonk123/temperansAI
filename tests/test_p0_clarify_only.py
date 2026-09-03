import pytest
from temperans.platform import TemperansPlatform

def payload(e,text='Investigate PROD-218'):
    return {'event_id':e,'workspace_id':'w','external_user_id':'u','surface':'generic_chatbot','conversation_id':e+'_c','content':{'text':text}}

def count_traj(rt):
    return rt.sqlite.conn.execute('SELECT COUNT(*) FROM trajectories WHERE organization_id=?',(rt.config.organization_id,)).fetchone()[0]

def test_clarify_only_config_is_persisted(tmp_path):
    p=TemperansPlatform(tmp_path/'p'); c=p.create_organization(organization_id='o',name='o',routing_mode='clarify_only')
    assert p.authenticate(c['api_key']).routing_mode=='clarify_only'

def test_clarify_only_new_is_non_mutating_and_pending(tmp_path):
    p=TemperansPlatform(tmp_path/'p'); c=p.create_organization(organization_id='o',name='o',routing_mode='clarify_only'); rt=p.runtime('o')
    r=p.observe_with_key(api_key=c['api_key'],payload=payload('e1'))
    assert r['decision']=='clarify' and r['proposed_decision']=='new' and r['requires_confirmation'] is True
    assert count_traj(rt)==0
    assert rt.sqlite.get_pending_proposal(organization_id='o',proposal_id=r['proposal_id'])['status']=='pending'

def test_clarify_only_duplicate_is_idempotent(tmp_path):
    p=TemperansPlatform(tmp_path/'p'); c=p.create_organization(organization_id='o',name='o',routing_mode='clarify_only')
    a=p.observe_with_key(api_key=c['api_key'],payload=payload('e1')); b=p.observe_with_key(api_key=c['api_key'],payload=payload('e1'))
    assert a==b and count_traj(p.runtime('o'))==0
    n=p.runtime('o').sqlite.conn.execute("SELECT COUNT(*) FROM pending_proposals WHERE organization_id='o'").fetchone()[0]
    assert n==1

def test_pending_survives_restart(tmp_path):
    root=tmp_path/'p'; p=TemperansPlatform(root); c=p.create_organization(organization_id='o',name='o',routing_mode='clarify_only')
    r=p.observe_with_key(api_key=c['api_key'],payload=payload('e1')); p2=TemperansPlatform(root); rt=p2.runtime('o')
    assert rt.sqlite.get_pending_proposal(organization_id='o',proposal_id=r['proposal_id'])['status']=='pending'
    assert count_traj(rt)==0

def test_reject_is_tenant_scoped_and_non_mutating(tmp_path):
    p=TemperansPlatform(tmp_path/'p'); a=p.create_organization(organization_id='a',name='a',routing_mode='clarify_only'); p.create_organization(organization_id='b',name='b',routing_mode='clarify_only')
    r=p.observe_with_key(api_key=a['api_key'],payload=payload('e1')); ra,rb=p.runtime('a'),p.runtime('b')
    with pytest.raises(KeyError): rb.sqlite.resolve_pending_proposal(organization_id='b',proposal_id=r['proposal_id'],status='rejected')
    row=ra.sqlite.resolve_pending_proposal(organization_id='a',proposal_id=r['proposal_id'],status='rejected')
    assert row['status']=='rejected' and count_traj(ra)==0
