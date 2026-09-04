from temperans.adjudication_cache import recovery_case_id
def test_case_id_changes_with_candidate_snapshot():
 e={"event_id":"e"}
 assert recovery_case_id(e,[{"trajectory_id":"a"}])!=recovery_case_id(e,[{"trajectory_id":"b"}])
