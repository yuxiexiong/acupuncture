#!/usr/bin/env python3
"""Check the upstream cache-only HTTP service; never send inference or agent requests."""
import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8791")
    args = parser.parse_args()
    result = {"url": args.url.rstrip("/"), "checked_at": datetime.now(timezone.utc).isoformat(), "checks": {}}
    current = "index"

    def get(path):
        with urlopen(result["url"] + path, timeout=30) as response:
            return json.load(response)

    try:
        index = get("/api/index")
        assert index["model"] == "Qwen/Qwen3.5-4B", "unexpected model"
        assert {k: index["arch"][k] for k in ("n_layers", "hidden", "inter")} == {
            "n_layers": 32, "hidden": 2560, "inter": 9216
        }, "unexpected architecture"
        assert isinstance(index["layers"], dict), "invalid sweep index"
        result["checks"][current] = {"model": index["model"], "sweep_layers": list(index["layers"])}

        current = "status"
        status = get("/api/status")["status"]
        # With weights disabled, missing caches cannot silently fall back to inference.
        assert status == "no model", "run with EXPLORER_NO_MODEL=1 for this cache-only check"
        result["checks"][current] = status

        current = "layout"
        layout = get("/api/layout?kind=writes")
        assert layout["available"] is True and layout["shape"] == [32, 9216], "missing or invalid layout"
        assert len(base64.b64decode(layout["cell"], validate=True)) == 32 * 9216 * 2, "invalid layout bytes"
        result["checks"][current] = {"shape": layout["shape"]}

        current = "lens"
        lens = get("/api/lens?layer=14&n=8949")
        for key in ("up", "down", "steer_up", "steer_down"):
            assert len(lens[key]) == 12 and all(isinstance(t, str) for t in lens[key]), f"invalid {key}"
        assert all(isinstance(lens[k], (int, float)) for k in ("kl_up", "kl_down")), "invalid KL values"
        result["checks"][current] = {"tokens_per_list": 12, "kl_up": lens["kl_up"], "kl_down": lens["kl_down"]}

        current = "connections"
        connections = get("/api/connections?layer=14&n=8949&k=24")
        for side in ("up", "down"):
            assert 0 < len(connections[side]) <= 24, f"missing {side} connections"
            for item in connections[side]:
                assert 0 <= item["layer"] < 32 and 0 <= item["n"] < 9216, "invalid connection coordinate"
                assert item["sign"] in (-1, 1) and isinstance(item["z"], (int, float)), "invalid connection score"
        result["checks"][current] = {side: len(connections[side]) for side in ("up", "down")}

        current = "search"
        search = get("/api/search?q=normal&limit=10")
        assert search["ready"] is True and 0 < len(search["results"]) <= 10, "missing search results"
        assert all({"layer", "n", "sign", "src", "lens"} <= item.keys() for item in search["results"]), "invalid search result"
        result["checks"][current] = {"returned": len(search["results"]), "total": search["total"]}
        result["status"] = "passed"
    except Exception as error:
        result.update(status="failed", failed_check=current, error=f"{type(error).__name__}: {error}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
