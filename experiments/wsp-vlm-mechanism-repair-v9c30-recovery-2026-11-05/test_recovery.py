"""CPU-only gates: reject uncertain or already completed actions."""
from copy import deepcopy
from resume_c import validate

good = dict(state=dict(repair_rounds_completed=26, research_done=False, frozen=None),
            pending=[], incomplete=[], failed_action_exists=False, amendment_exists=False,
            alive=True, code_matches=True, last_action='turn-0142',
            last_response={'id': 'turn-0142'}, expected_response={'id': 'turn-0142'})
events = [dict(type='thread.started', thread_id='same-thread'),
          dict(type='turn.failed', error=dict(message='Selected model is at capacity. Please try a different model.'))]
receipt = dict(thread='same-thread')
validate(good, events, receipt)
for key, value in [('pending', ['turn-0143']), ('incomplete', ['turn-0142']),
                   ('failed_action_exists', True), ('amendment_exists', True),
                   ('alive', False), ('code_matches', False), ('last_action', 'turn-0144'),
                   ('last_response', {'id': 'different'})]:
    bad = deepcopy(good)
    bad[key] = value
    try:
        validate(bad, events, receipt)
    except ValueError:
        pass
    else:
        raise AssertionError(key)
for extra in [dict(type='turn.completed'), dict(type='item.completed', item=dict(type='agent_message'))]:
    try:
        validate(good, events + [extra], receipt)
    except ValueError:
        pass
    else:
        raise AssertionError(extra)
print('PASS: valid boundary and 10 unsafe-boundary rejections; no model calls')
