"""Temperans V1 verification report."""
import json,subprocess,sys
def main():
 p=subprocess.run([sys.executable,"-m","pytest","-q"],capture_output=True,text=True)
 report={"v1_verification_version":"v1","pytest_pass":p.returncode==0,
         "pytest_summary":p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "",
         "gates":{"live_import_replay":"covered_by_regression",
                  "tenant_isolation":"covered_by_regression",
                  "l2_non_authority":"covered_by_regression",
                  "provider_resilience":"covered_by_regression"},
         "human_audit":{"status":"REQUIRED_NOT_RUN","acceptance":">=70% trajectories correct; zero false merges in frozen audit sample"},
         "milestone_a_complete":False}
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()
