#!/usr/bin/env python3
"""Bounded per-model acceptance from PROTOCOL.zh-CN.md; retain requests, raw replies and failures."""
import argparse
import base64
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import struct
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("2b", "4b", "9b"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    models = json.loads((Path(__file__).resolve().parent / "models.json").read_text())
    model = next(m for m in models if m["id"] == args.profile)
    url = f"http://127.0.0.1:{model['port']}"
    layers, neurons = model["layers"], model["inter"]
    receipt = {"started_at": datetime.now(timezone.utc).isoformat(), "model": model,
               "url": url, "checks": [], "status": "started"}
    # Exclusive creation reserves a new receipt before making any service request.
    with args.output.open("x", encoding="utf-8") as output:
        def save():
            output.seek(0)
            json.dump(receipt, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.truncate()
            output.flush()

        def request(name, path, payload=None, binary=False, expected_status=200):
            entry = {"name": name, "path": path, "request": payload, "expected_http_status": expected_status}
            receipt["checks"].append(entry)
            save()
            started = time.monotonic()
            req = Request(url + path, data=json.dumps(payload).encode() if payload is not None else None,
                          headers={"Content-Type": "application/json"})
            try:
                try:
                    response = urlopen(req, timeout=180)
                except HTTPError as error:
                    response = error
                with response:
                    entry["http_status"] = response.status
                    entry["response_headers"] = dict(response.headers)
                    data = response.read()
                if binary:
                    entry["raw_response_base64"] = base64.b64encode(data).decode()
                else:
                    entry["raw_response"] = data.decode()
                assert entry["http_status"] == expected_status, f"unexpected HTTP status in {name}"
                if binary:
                    return data
                return entry["raw_response"] if path == "/api/steer" else json.loads(entry["raw_response"])
            finally:
                entry["elapsed_seconds"] = time.monotonic() - started
                save()

        def valid(layer, neuron):
            return isinstance(layer, int) and isinstance(neuron, int) and 0 <= layer < layers and 0 <= neuron < neurons

        try:
            index = request("index", "/api/index")
            assert index["model"] == model["repo"] and index["profile"] == args.profile
            assert {k: index["arch"][k] for k in ("n_layers", "hidden", "inter")} == {
                "n_layers": layers, "hidden": model["hidden"], "inter": neurons}
            assert index["models"] == [{k: m[k] for k in ("id", "label", "port")} for m in models]
            assert index["status"] == "ready", "wait for model and cache preparation before acceptance"

            layout = request("layout", "/api/layout?kind=writes")
            assert layout["available"] and layout["shape"] == [layers, neurons]
            data = base64.b64decode(layout["cell"], validate=True)
            assert len(data) == layers * neurons * 2
            cells = [v[0] for v in struct.iter_unpack("<h", data)]
            side = math.ceil(math.sqrt(neurons))
            for layer in range(layers):
                row = cells[layer * neurons:(layer + 1) * neurons]
                assert len(set(row)) == neurons and all(0 <= cell < side * side for cell in row)

            lens = request("lens", "/api/lens?layer=10&n=100")
            for key in ("up", "down", "steer_up", "steer_down"):
                assert len(lens[key]) == 12 and all(isinstance(token, str) for token in lens[key]), key
            assert all(math.isfinite(lens[key]) for key in ("kl_up", "kl_down"))

            connections = request("connections", "/api/connections?layer=10&n=100")
            for direction in ("up", "down"):
                assert len(connections[direction]) == 24
                for item in connections[direction]:
                    assert valid(item["layer"], item["n"]) and item["sign"] in (-1, 1)
                    assert math.isfinite(item["z"])
                    assert item["layer"] < 10 if direction == "up" else item["layer"] > 10

            web = request("web", "/api/web?layer=10&n=100", binary=True)
            assert web and len(web) % 12 == 0
            for source_layer, source_n, dest_layer, dest_n, score, hop in struct.iter_unpack("<6h", web):
                assert valid(source_layer, source_n) and valid(dest_layer, dest_n)
                assert source_layer < dest_layer and hop != 0
            receipt["checks"][-1]["link_count"] = len(web) // 12

            search = request("search", "/api/search?q=normal&limit=10")
            assert search["ready"] and isinstance(search["results"], list) and len(search["results"]) <= 10
            assert all(valid(item["layer"], item["n"]) for item in search["results"])
            read = request("natural_read", "/api/reads", {
                "layer": 10, "n": 100, "text": "The sky is blue.", "chat": False})
            assert read["units"] and all(math.isfinite(unit["act"]) for unit in read["units"])
            assert all(math.isfinite(piece) for unit in read["units"] for piece in unit["pieces"])
            infer = request("natural_map", "/api/infer", {"text": "The sky is blue.", "chat": False})
            assert infer["ready"] and len(infer["tokens"]) == len(infer["pos"]) > 0
            view = request("natural_map_values", "/api/infer/view?limit=10")
            assert view["shape"] == [layers, neurons]
            map_data = base64.b64decode(view["map"], validate=True)
            assert len(map_data) == layers * neurons * 2
            assert all(math.isfinite(value[0]) for value in struct.iter_unpack("<e", map_data))

            for dose in (0, 0.1):
                raw = request(f"steer_{dose}", "/api/steer", {
                    "layer": 10, "n": 100, "prompt": "Name two colors.", "dose": dose, "mode": "add", "max_new": 12})
                events = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith("data: ")]
                assert events and events[-1]["row"] is None, "stream did not finish"
                assert not any("error" in event for event in events), "steering error"
                assert all(event["row"] in (0, 1, 2, None) for event in events)
                texts = ["".join(event["t"] for event in events if event["row"] == row) for row in range(3)]
                receipt["checks"][-1]["texts"] = texts
                receipt["checks"][-1]["emitted_chunks"] = [sum(event["row"] == row for event in events) for row in range(3)]
                assert all(texts), "empty generation"
                if dose == 0:
                    assert len(set(texts)) == 1, "zero-dose columns differ"

            for layer, neuron in ((-1, 100), (layers, 100), (10, -1), (10, neurons)):
                request(f"reject_L{layer}_N{neuron}", f"/api/unit?layer={layer}&n={neuron}", expected_status=400)
            receipt["status"] = "passed"
        except (Exception, KeyboardInterrupt) as error:
            receipt.update(status="failed", failed_check=receipt["checks"][-1]["name"] if receipt["checks"] else None,
                           error=f"{type(error).__name__}: {error}")
        finally:
            receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
            save()
    print(json.dumps({"status": receipt["status"], "profile": args.profile, "file": str(args.output),
                      "error": receipt.get("error")}, ensure_ascii=False))
    return 0 if receipt["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
