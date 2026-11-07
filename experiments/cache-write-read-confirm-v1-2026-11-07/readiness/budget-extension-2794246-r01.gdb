set pagination off
set confirm off
set scheduler-locking off
set $gil = (int) PyGILState_Ensure()
call (int) PyRun_SimpleString("exec('ns={\"__name__\":\"dwc_budget_extension_r01\"}; exec(compile(open(\\'/workspace/acupuncture/experiments/cache-write-read-confirm-v1-2026-11-07/readiness/budget_extension_r01.py\\').read(),\"dwc_budget_extension_r01\",\"exec\"), ns); ns[\"apply\"]()', {})")
call (void) PyGILState_Release($gil)
detach
quit
