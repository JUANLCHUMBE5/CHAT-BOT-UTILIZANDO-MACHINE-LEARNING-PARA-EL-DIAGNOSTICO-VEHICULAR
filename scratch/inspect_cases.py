import csv
import sys

sys.stdout.reconfigure(encoding="utf-8")
with open("FASE11_TURN_TRACE_V1.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"] in ("CASE_007", "CASE_009", "CASE_010"):
            print(f"Case: {r['case_id']}")
            print(f"  Input: {r['user_input']}")
            print(f"  Synth: {r['synthesized_ml_query']}")
            print(f"  Top1:  {r['fault_top1']}")
            print(f"  Resp:  {r['final_response'][:120]}")
            print()
