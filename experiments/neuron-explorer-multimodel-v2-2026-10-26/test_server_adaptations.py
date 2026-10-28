#!/usr/bin/env python3
"""Routing, identity and isolation checks; run with the server's Python, without loading weights."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
MODELS = json.loads((ROOT / "models.json").read_text())


def check_profile(profile, data_root):
    model = next(m for m in MODELS if m["id"] == profile)
    data = Path(data_root) / profile
    os.environ.update(
        EXPLORER_PROFILE=profile,
        EXPLORER_MODEL=model["path"],
        EXPLORER_MODEL_ID=model["repo"],
        EXPLORER_DATA=str(data),
        EXPLORER_NO_MODEL="1",
        PORT=str(model["port"]),
        CUDA_VISIBLE_DEVICES="",
        HF_HUB_OFFLINE="1",
        HF_DATASETS_OFFLINE="1",
    )
    sys.path.insert(0, str(ROOT / "upstream" / "explorer"))
    from fastapi.testclient import TestClient
    import server

    # No lifespan: these routes need configuration and temporary files, not tokenizer/cache startup work.
    client = TestClient(server.app, base_url=f"http://127.0.0.1:{model['port']}")
    config = json.loads((Path(model["path"]) / "config.json").read_text())["text_config"]
    index = client.get("/api/index").json()
    assert index["profile"] == profile and index["model"] == model["repo"]
    assert index["models"] == [{k: m[k] for k in ("id", "label", "port")} for m in MODELS]
    for field, cfg_field, manifest_field in (
        ("n_layers", "num_hidden_layers", "layers"),
        ("hidden", "hidden_size", "hidden"),
        ("inter", "intermediate_size", "inter"),
    ):
        assert index["arch"][field] == config[cfg_field] == model[manifest_field]

    for layer, neuron in ((-1, 0), (model["layers"], 0), (0, -1), (0, model["inter"])):
        assert client.get("/api/unit", params={"layer": layer, "n": neuron}).status_code == 400
        assert client.post("/api/name", json={"layer": layer, "n": neuron, "name": "invalid"}).status_code == 400
    for invalid in (1.9, True, "not-a-number"):
        assert client.post("/api/name", json={"layer": 0, "n": invalid, "name": "invalid"}).status_code == 400
    assert client.get("/api/unit", params={"layer": model["layers"] - 1, "n": model["inter"] - 1}).status_code == 200
    assert client.get("/api/unit", params={"layer": 14, "n": 8949}).status_code == (400 if profile == "2b" else 200)

    assert client.get("/api/unit", params={"layer": 0, "n": 0}).json()["name"] == f"initial-{profile}"
    assert client.post("/api/name", json={"layer": 0, "n": 0, "name": f"tested-{profile}"}).status_code == 200
    assert client.get("/api/unit", params={"layer": 0, "n": 0}).json()["name"] == f"tested-{profile}"
    assert Path(server.NAMES) == data / "names.json"
    assert Path(server.CACHE) == data / "cache"

    navigation = {"sec-fetch-site": "same-site", "sec-fetch-mode": "navigate", "sec-fetch-dest": "document"}
    assert client.get("/", headers=navigation).status_code == 200
    assert client.get("/api/index", headers=navigation).status_code == 403
    assert client.get("/api/index", headers={"sec-fetch-site": "same-site"}).status_code == 403
    assert client.get("/api/index", headers={"sec-fetch-site": "cross-site"}).status_code == 403
    assert client.get("/", headers={**navigation, "sec-fetch-site": "cross-site"}).status_code == 403
    assert client.post("/", headers=navigation).status_code == 403
    assert client.get("/api/index", headers={"origin": "https://example.invalid"}).status_code == 403
    assert client.get("/api/index", headers={"host": f"example.invalid:{model['port']}"}).status_code == 403
    assert client.get("/api/index", headers={"sec-fetch-site": "same-origin"}).status_code == 200
    assert server.NO_MODEL and server.rt.model is None
    client.close()
    server.rt._db.close()
    print(json.dumps({"profile": profile, "status": "passed", "model_loaded": False,
                      "shape": [model["layers"], model["inter"]]}))


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--profile":
        check_profile(sys.argv[2], sys.argv[3])
        return
    assert len(sys.argv) == 1, "Run without arguments; profile children are internal."
    results = []
    with tempfile.TemporaryDirectory(prefix="acupuncture-explorer-check-") as directory:
        data_root = Path(directory)
        for model in MODELS:
            data = data_root / model["id"]
            data.mkdir()
            (data / "names.json").write_text(json.dumps({"L0/N0": f"initial-{model['id']}"}))
        for model in MODELS:
            profile = model["id"]
            previous = {m["id"]: (data_root / m["id"] / "names.json").read_bytes() for m in MODELS}
            child = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--profile", profile, directory],
                                   text=True, capture_output=True)
            assert child.returncode == 0, f"{profile}: {child.stdout}\n{child.stderr}"
            results.append(json.loads(child.stdout))
            for other, contents in previous.items():
                if other != profile:
                    assert (data_root / other / "names.json").read_bytes() == contents, "cross-model name mutation"
        assert len({(data_root / m["id"] / "names.json").read_text() for m in MODELS}) == len(MODELS)
    print(json.dumps({"status": "passed", "profiles": results, "names_isolated": True,
                      "separate_process_per_profile": True, "model_inference_run": False}, indent=2))


if __name__ == "__main__":
    main()
