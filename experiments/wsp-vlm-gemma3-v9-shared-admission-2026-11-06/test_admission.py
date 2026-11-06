from queue_shared import eligible

peer = dict(stage='search', pid=123)
assert eligible(peer, True, 36864, [123])
assert not eligible(peer, True, 36863, [123])
assert not eligible(peer, False, 70000, [123])
assert not eligible(dict(stage='engineering', pid=123), True, 70000, [123])
assert not eligible(peer, True, 70000, [123, 456])
assert not eligible(peer, True, 70000, [])
assert not eligible(peer, True, 70000, [456])
print('PASS: capacity, accepted peer, science stage, and unrelated process rejection')
