"""Runs only inside the restricted filesystem/network namespace created by the driver."""
import json
import sys

from execution import check_correctness


case = json.load(sys.stdin)
problem, completion = case["problem"], case["completion"]
program = problem["prompt"] + completion + "\n" + problem["test"] + "\ncheck(" + problem["entry_point"] + ")"
syntax_error = False
try:
    compile(program, "<humaneval>", "exec")
except SyntaxError:
    syntax_error = True
result = check_correctness(problem, completion, 3.0, completion_id=0)
result["category"] = ("passed" if result["passed"] else "syntax_error" if syntax_error
                      else "timeout" if result["result"] == "timed out" else "test_failure")
print(json.dumps(result))
