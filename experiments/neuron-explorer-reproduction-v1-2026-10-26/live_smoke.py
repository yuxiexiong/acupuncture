#!/usr/bin/env python3
"""Bounded live checks from PROTOCOL.zh-CN.md; keep every request and raw response."""
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

output = Path(sys.argv[1])
if output.exists():
    raise SystemExit(f"Keep prior evidence; choose a new output: {output}")
receipt = {"started_at": datetime.now(timezone.utc).isoformat(), "checks": [], "status": "started"}


def request(name, path, payload=None):
    entry = {"name": name, "path": path, "request": payload}
    receipt["checks"].append(entry)
    start = time.monotonic()
    req = Request("http://127.0.0.1:8791" + path,
                  data=json.dumps(payload).encode() if payload is not None else None,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=180) as response:
        entry["raw_response"] = response.read().decode()
    entry["elapsed_seconds"] = time.monotonic() - start
    if path == "/api/steer":
        events = [json.loads(line[6:]) for line in entry["raw_response"].splitlines() if line.startswith("data: ")]
        assert events and events[-1]["row"] is None, "stream did not finish"
        assert not any("error" in event for event in events), "steering returned an error"
        texts = ["".join(event["t"] for event in events if event["row"] == row) for row in range(3)]
        entry["texts"] = texts
        assert all(texts), "empty generation"
        return texts
    return json.loads(entry["raw_response"])


try:
    assert request("status", "/api/status")["status"] == "ready"
    read = request("natural_read", "/api/reads", {"layer": 14, "n": 8949, "text": "The sky is blue.", "chat": False})
    assert read["units"] and all(math.isfinite(unit["act"]) for unit in read["units"])
    infer = request("natural_map", "/api/infer", {"text": "The sky is blue.", "chat": False})
    assert infer["ready"] and len(infer["tokens"]) == len(infer["pos"]) > 0
    view = request("natural_map_values", "/api/infer/view?limit=10")
    assert view["shape"] == [32, 9216] and view["map"]
    for dose in (0, 0.1):
        texts = request(f"steer_{dose}", "/api/steer", {
            "layer": 14, "n": 8949, "prompt": "Name two colors.", "dose": dose, "mode": "add", "max_new": 12})
        if dose == 0:
            assert len(set(texts)) == 1, "zero-dose rows differ"
    receipt["status"] = "passed"
except Exception as error:
    receipt.update(status="failed", error=f"{type(error).__name__}: {error}")
finally:
    receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": receipt["status"], "file": str(output), "error": receipt.get("error")}, ensure_ascii=False))
raise SystemExit(0 if receipt["status"] == "passed" else 1)
