"""Frozen extraction and isolated MBPP / upstream EvalPlus scoring."""
import argparse
import contextlib
import io
import json
import re
import time


def extract(text, thinking=True):
    if thinking and '</think>' not in text:
        return None, 'unfinished_thinking'
    answer = text.rsplit('</think>', 1)[-1]
    blocks = re.findall(r'```(?:python[ \t]*|[ \t]*)\r?\n(.*?)```', answer, re.S | re.I)
    code = blocks[-1] if blocks else answer
    return code.strip(), None


def mbpp(task, code):
    ns, checks = {}, []
    try:
        compile(code, '<candidate>', 'exec')
    except SyntaxError as exc:
        return dict(status='syntax_error', correct=False, error=str(exc), tests=[])
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(task.get('test_setup_code', ''), ns)
            exec(code, ns)
    except BaseException as exc:
        return dict(status='runtime_error', correct=False, error=type(exc).__name__+': '+str(exc), tests=[])
    for test in task['test_list']:
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                exec(test, ns)
            checks.append(dict(test=test, passed=True))
        except BaseException as exc:
            checks.append(dict(test=test, passed=False, error=type(exc).__name__+': '+str(exc)))
    passed = all(x['passed'] for x in checks) and bool(checks)
    return dict(status='pass' if passed else 'test_failure', correct=passed, tests=checks)


def humaneval(task, code):
    # Reuse upstream comparisons, float tolerances, special oracle and timeout logic.
    from evalplus.eval import untrusted_check
    from evalplus.gen.util import trusted_exec
    reference = task['prompt'] + task['canonical_solution']
    result = {}
    for group in ('base', 'plus'):
        inputs = task[group+'_input']
        expected, times = trusted_exec(reference, inputs, task['entry_point'], record_time=True)
        status, details = untrusted_check('humaneval', code, inputs, task['entry_point'],
            expected=expected, atol=task['atol'], ref_time=times, fast_check=False)
        result[group] = dict(status=status, total=len(inputs), tested=len(details),
                             passed=sum(bool(v) for v in details), details=[bool(v) for v in details],
                             reference_seconds=sum(times))
    ok = all(v['status']=='pass' for v in result.values())
    return dict(status='pass' if ok else 'test_failure', correct=ok, groups=result)


def main():
    request = json.load(__import__('sys').stdin)
    start = time.monotonic()
    if request['kind']=='probe':
        ns = {}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(request['code'], ns)
        result = ns['result']
    else:
        task = request['task']
        if request.get('reference'):
            code = task['code'] if request['kind']=='mbpp' else task['prompt']+task['canonical_solution']
        else:
            code, error = extract(request['text'], request.get('thinking', True))
            if error:
                print(json.dumps(dict(status=error, correct=False)))
                return
        result = mbpp(task, code) if request['kind']=='mbpp' else humaneval(task, code)
    result['seconds'] = time.monotonic()-start
    print(json.dumps(result, allow_nan=False))


if __name__=='__main__':
    main()
