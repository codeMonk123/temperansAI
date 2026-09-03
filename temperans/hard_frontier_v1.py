"""Frozen Hard Frontier V1 benchmark.
40 cases: 10 NEW, 10 ATTACH, 10 BRANCH, 10 ABSTAIN across hard categories.
Synthetic candidate IDs are stable evaluation identifiers.
"""
def _c(cid, goal, state, context, anchors=None):
    return {"trajectory_id":cid,"durable_goal":goal,"current_state":state,
            "recent_context":context,"anchors":anchors or []}

def _e(eid,text,surface="generic_chatbot"):
    return {"event_id":eid,"workspace_id":"production","external_user_id":"hard_user",
            "conversation_id":eid+"_conv","surface":surface,"content":{"text":text}}

def build_hard_frontier():
    cases=[]
    def add(cid,cat,text,cands,action,target=None):
        cases.append({"case_id":cid,"category":cat,"event":_e(cid,text),
                      "candidate_views":cands,"gold_action":action,
                      "gold_candidate_id":target})
    # Reusable candidates.
    prod=_c("t_prod","restore production checkout","certificate failure blocks checkout",
            ["rotated certificate","deployment still failing"])
    auth=_c("t_auth","fix employee login","SSO redirect loop",["IdP metadata changed"])
    stage=_c("t_stage","fix staging login","staging SSO timeout",["only staging affected"])
    data=_c("t_data","repair nightly warehouse load","orders table missing rows",
            ["backfill attempted","row counts still low"])
    mobile=_c("t_mobile","ship mobile referral tracking","deep link attribution missing",
              ["Branch SDK instrumentation"])
    # 1 anchor removed / semantic continuation: ATTACH
    for i,text in enumerate([
      "the certificate issue is back after the restart",
      "checkout is still blocked by the TLS problem",
      "same production deploy problem after rotating the cert",
      "the fix from earlier did not restore checkout",
      "still failing after that certificate change"],1):
        add(f"anchor_removed_attach_{i}","anchor_removed",text,[prod,auth,data],"attach","t_prod")
    # 2 different topic words, same work: ATTACH
    for i,text in enumerate([
      "customers cannot pay because the browser rejects our endpoint",
      "the release remains blocked even though the service is healthy",
      "we need to roll back the credential change from this morning",
      "the web client now reports trust errors",
      "production checkout remains unavailable after deployment"],1):
        add(f"semantic_attach_{i}","different_topic_same_work",text,[prod,auth,data],"attach","t_prod")
    # 3 same topic, genuinely NEW
    for i,text in enumerate([
      "new login incident for the vendor portal; unrelated to employee SSO",
      "production login for customers is failing; employee SSO is healthy",
      "start investigating a separate staging authentication outage",
      "another customer reports an independent password reset failure",
      "new OAuth problem in the partner console, separate from current SSO work"],1):
        add(f"same_topic_new_{i}","same_topic_different_work",text,[auth,stage,prod],"new")
    # 4 misleading similarity: NEW
    for i,text in enumerate([
      "nightly orders load is missing rows in the EU warehouse, separate pipeline",
      "orders table is incomplete in a new analytics workspace",
      "backfill failed for marketing events, unrelated to the orders pipeline",
      "row counts are low in the billing export, start separate investigation",
      "warehouse load issue for inventory, not the existing orders incident"],1):
        add(f"misleading_new_{i}","misleading_similarity",text,[data,prod,mobile],"new")
    # 5 BRANCH from existing work
    for i,text in enumerate([
      "checkout cert is fixed; separately branch work to automate certificate rotation",
      "while resolving checkout, create a related branch to add expiry monitoring",
      "same incident uncovered a separate certificate renewal workflow we should build",
      "branch from the production cert issue to improve secret rotation tooling",
      "related follow-up: build proactive certificate alerts as separate work"],1):
        add(f"branch_{i}","branch",text,[prod,auth,data],"branch","t_prod")
    # 6 reopen-like continuation: ATTACH (lifecycle semantics represented in context)
    resolved=dict(prod);resolved["lifecycle"]="resolved";resolved["recent_context"]=prod["recent_context"]+["resolved yesterday"]
    for i,text in enumerate([
      "checkout trust error returned this morning",
      "the production certificate failure has come back",
      "same checkout outage reopened after yesterday's resolution",
      "customers again see the trust warning we fixed",
      "reopen the checkout certificate work; symptoms returned"],1):
        add(f"reopen_{i}","reopen",text,[resolved,auth,data],"attach","t_prod")
    # 7 sparse ambiguous references: ABSTAIN
    for i,text in enumerate([
      "still broken after that change",
      "same thing again",
      "continue with the issue from earlier",
      "that fix did not work",
      "can we pick this back up"],1):
        add(f"sparse_abstain_{i}","sparse_reference",text,[prod,auth,data],"abstain")
    # 8 genuine ambiguity between near candidates: ABSTAIN
    for i,text in enumerate([
      "the login timeout is happening again",
      "authentication is still slow",
      "SSO failed after the latest change",
      "users still cannot sign in",
      "the identity issue remains unresolved"],1):
        add(f"competing_abstain_{i}","competing_candidates",text,[auth,stage,prod],"abstain")
    assert len(cases)==40
    return cases
