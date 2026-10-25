"""Frozen clean ridge mapping, stratified random sources, and one-column target matching."""
import argparse
import json
import math
import os
from pathlib import Path
import random
import time
import traceback

from collect_activations import sha, utc, write_json
from transfer_engine import LAYERS, SOURCE_NEURONS, SIGNS


def load_collection(directory):
    import torch
    directory = Path(directory)
    receipt = json.loads((directory / "receipt.json").read_text())
    assert receipt["status"] == "completed"
    for name, digest in receipt["files"].items():
        assert sha(directory / name) == digest
    index = json.loads((directory / "index.json").read_text())
    columns = torch.load(directory / "columns.pt", map_location="cpu", weights_only=True)
    rms = torch.load(directory / "natural_rms.pt", map_location="cpu", weights_only=True)
    return directory, receipt, index, columns, rms


def paired_arrays(source, target, layer, split, device):
    import torch
    sx, ty, weights, doc_ids = [], [], [], []
    sdir, _, sindex, _, _ = source
    tdir, _, tindex, _, _ = target
    assert [x["id"] for x in sindex[split]] == [x["id"] for x in tindex[split]]
    for document, (sentry, tentry) in enumerate(zip(sindex[split], tindex[split])):
        for directory, entry in ((sdir, sentry), (tdir, tentry)):
            assert sha(directory / entry["file"]) == entry["sha256"]
        a = torch.load(sdir / sentry["file"], map_location="cpu", weights_only=True)
        b = torch.load(tdir / tentry["file"], map_location="cpu", weights_only=True)
        assert a["text_sha256"] == b["text_sha256"] and a["tokens"] == b["tokens"] and a["positions"] == b["positions"], "Token/position alignment differs; no ordinal fallback is allowed"
        x, y = a["layers"][str(layer)]["residual"], b["layers"][str(layer)]["residual"]
        assert len(x) == len(y) and len(x) > 0
        sx.append(x)
        ty.append(y)
        weights.append(torch.full((len(x),), 1.0 / (len(sindex[split]) * len(x))))
        doc_ids.extend([document] * len(x))
    return (torch.cat(sx).to(device), torch.cat(ty).to(device), torch.cat(weights).to(device),
            torch.tensor(doc_ids, device=device))


def ridge_statistics(x, y, weights):
    import torch
    weights = weights / weights.sum()
    mu_x, mu_y = weights @ x, weights @ y
    centered_x, centered_y = x - mu_x, y - mu_y
    scale_x = (weights @ centered_x.square().sum(1) / x.shape[1]).sqrt()
    scale_y = (weights @ centered_y.square().sum(1) / y.shape[1]).sqrt()
    assert scale_x > 0 and scale_y > 0
    xn, yn = centered_x / scale_x, centered_y / scale_y
    gram = xn.T @ (weights[:, None] * xn)
    rhs = xn.T @ (weights[:, None] * yn)
    # FP64 solve prevents the smallest declared ridge from being swallowed by FP32 factorization.
    return mu_x, mu_y, scale_x, scale_y, gram.double(), rhs.double()


def solve_ridge(stats, regularization):
    import torch
    mu_x, mu_y, sx, sy, gram, rhs = stats
    system = gram + regularization * torch.eye(gram.shape[0], dtype=gram.dtype, device=gram.device)
    b = torch.linalg.solve(system, rhs).float()
    matrix = (sy / sx) * b.T
    bias = mu_y - matrix @ mu_x
    assert torch.isfinite(matrix).all() and torch.isfinite(bias).all()
    return matrix, bias


def relative_mse(matrix, bias, x, y, weights, target_training_mean):
    import torch
    numerator = torch.zeros((), device=x.device)
    denominator = torch.zeros((), device=x.device)
    for start in range(0, len(x), 1024):
        end = start + 1024
        predicted = x[start:end] @ matrix.T + bias
        numerator += weights[start:end] @ (predicted - y[start:end]).square().sum(1)
        denominator += weights[start:end] @ (y[start:end] - target_training_mean).square().sum(1)
    assert denominator > 0
    return float(numerator / denominator)


def quintiles(values):
    import torch
    cuts = torch.quantile(values.float(), torch.tensor([.2, .4, .6, .8]))
    return torch.bucketize(values.float(), cuts, right=False)


def random_sources(columns, natural_rms):
    rng = random.Random(20261026)
    selected, audit = {}, {}
    for layer in LAYERS:
        key, true_index = str(layer), SOURCE_NEURONS[layer]
        norms = columns[key].norm(dim=0)
        norm_bins, activation_bins = quintiles(norms), quintiles(natural_rms[key])
        nb, ab = int(norm_bins[true_index]), int(activation_bins[true_index])
        order_a = sorted(range(5), key=lambda i: (abs(i - ab), i))
        order_n = sorted(range(5), key=lambda i: (abs(i - nb), i))
        allowed_a, allowed_n = [ab], [nb]
        def pool():
            return [i for i in range(len(norms)) if i != true_index and norms[i] > 0
                    and int(norm_bins[i]) in allowed_n and int(activation_bins[i]) in allowed_a]
        candidates = pool()
        for abin in order_a[1:]:
            if len(candidates) >= 3:
                break
            allowed_a.append(abin)
            candidates = pool()
        for nbin in order_n[1:]:
            if len(candidates) >= 3:
                break
            allowed_n.append(nbin)
            candidates = pool()
        assert len(candidates) >= 3
        selected[key] = rng.sample(candidates, 3)
        audit[key] = {"true_index": true_index, "true_norm_quintile": nb, "true_activation_quintile": ab,
                      "allowed_norm_bins": allowed_n, "allowed_activation_bins": allowed_a,
                      "candidate_pool": candidates, "selected": selected[key]}
    pairs = {"true": {str(layer): SOURCE_NEURONS[layer] for layer in LAYERS}}
    pairs.update({f"random{i + 1}": {str(layer): selected[str(layer)][i] for layer in LAYERS} for i in range(3)})
    return pairs, audit


def target_condition(unit_source, matrix, target_columns):
    import torch
    mapped = matrix @ unit_source
    mapped_norm = mapped.norm()
    assert torch.isfinite(mapped).all() and mapped_norm > 0, "Degenerate mapped direction"
    norms = target_columns.norm(dim=0)
    valid = norms > 0
    unit_columns = target_columns / norms.clamp_min(torch.finfo(norms.dtype).tiny)
    projections = mapped @ unit_columns
    projections[~valid] = 0
    index = int(projections.abs().argmax())
    beta = projections[index]
    assert beta != 0 and valid[index], "No nonzero target projection"
    sign, norm = float(beta.sign()), float(norms[index])
    specs = {
        "D_raw": {"kind": "vector", "vector": mapped.cpu(), "scale": "source", "coefficient": 1.0},
        "S_proj": {"kind": "channel", "index": index, "scale": "source", "coefficient": float(beta) / norm},
        "D_match": {"kind": "vector", "vector": (mapped / mapped_norm).cpu(), "scale": "target", "coefficient": 1.0},
        "S_recipe": {"kind": "channel", "index": index, "scale": "target", "coefficient": sign / norm}}
    rho = float(beta.square() / mapped_norm.square())
    audit = {"index": index, "sign": sign, "source_unit_to_target_norm": float(mapped_norm),
             "beta_per_unit_source_scale": float(beta), "target_column_norm": norm,
             "reconstruction_fraction": rho, "relative_residual_squared": 1 - rho}
    return specs, audit, mapped


def native_baselines(target):
    import torch
    directory, _, index, columns_payload, _ = target
    columns = columns_payload["columns"]
    rows = []
    for entry in index["contrast"]:
        assert sha(directory / entry["file"]) == entry["sha256"]
        rows.append(torch.load(directory / entry["file"], map_location="cpu", weights_only=True))
    scenarios = sorted({row["scenario_id"] for row in rows})
    assert len(scenarios) == 32 and len(rows) == 128
    for scenario in scenarios:
        assert {(r["stance"], r["style"]) for r in rows if r["scenario_id"] == scenario} == {
            (a, b) for a in ("harmful", "neutral") for b in ("hostile", "neutral")}
    conditions, audit, vectors = {"T_dense": {}, "T_sparse": {}}, {}, {}
    for layer in LAYERS:
        key = str(layer)
        dense = sum((1.0 if r["stance"] == "harmful" else -1.0) * r["layers"][key]["residual_mean"] for r in rows) / 64
        activation = sum((1.0 if r["stance"] == "harmful" else -1.0) * r["layers"][key]["activation_mean"] for r in rows) / 64
        assert dense.norm() > 0 and torch.isfinite(dense).all()
        sparse_index = int(activation.abs().argmax())
        norm = columns[key][:, sparse_index].norm()
        assert norm > 0 and activation[sparse_index] != 0
        conditions["T_dense"][key] = {"kind": "vector", "vector": dense / dense.norm(), "scale": "target", "coefficient": 1.0}
        conditions["T_sparse"][key] = {"kind": "channel", "index": sparse_index, "scale": "target", "coefficient": float(activation[sparse_index].sign() / norm)}
        audit[key] = {"dense_norm": float(dense.norm()), "sparse_index": sparse_index,
                      "sparse_sign": float(activation[sparse_index].sign()), "sparse_activation_difference": float(activation[sparse_index])}
        vectors[key] = dense
    return conditions, audit, vectors


def run(args):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)
    torch.manual_seed(0)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "running", "started_utc": utc(), "arguments": vars(args),
               "source_sha256": {name: sha(Path(__file__).parent / name) for name in ("fit_mapping.py", "transfer_engine.py", "collect_activations.py")}}
    write_json(output / "receipt.json", receipt)
    started = time.monotonic()
    try:
        source, target = load_collection(args.source), load_collection(args.target)
        receipt["source_collection_sha256"] = sha(Path(args.source) / "receipt.json")
        receipt["target_collection_sha256"] = sha(Path(args.target) / "receipt.json")
        source_columns, target_columns = source[3]["columns"], target[3]["columns"]
        pairs, random_audit = random_sources(source_columns, source[4])
        write_json(output / "random_sources.json", {"seed": 20261026, "pairs": pairs, "sampling": random_audit})
        conditions = {"T_0": {}}
        selection, mapping_audit, mapped_vectors = {}, {}, {}
        for layer in LAYERS:
            key = str(layer)
            x, y, p, docs = paired_arrays(source, target, layer, "map_train", args.device)
            vx, vy, vp, _ = paired_arrays(source, target, layer, "map_val", args.device)
            stats = ridge_statistics(x, y, p)
            candidates = []
            for regularization in (1e-4, 1e-2, 1.0):
                matrix, bias = solve_ridge(stats, regularization)
                error = relative_mse(matrix, bias, vx, vy, vp, stats[1])
                assert math.isfinite(error)
                candidates.append((error, -regularization))
            error, negative_regularization = min(candidates)
            regularization = -negative_regularization
            matrix, bias = solve_ridge(stats, regularization)
            torch.save({"matrix": matrix.cpu(), "bias": bias.cpu(), "lambda": regularization,
                        "source_mean": stats[0].cpu(), "target_mean": stats[1].cpu(),
                        "source_scalar_rms": float(stats[2]), "target_scalar_rms": float(stats[3])}, output / f"map-L{layer}.pt")
            halves = []
            midpoint = len(source[2]["map_train"]) // 2
            for mask in (docs < midpoint, docs >= midpoint):
                half_matrix, _ = solve_ridge(ridge_statistics(x[mask], y[mask], p[mask]), regularization)
                halves.append(half_matrix)
            eigenvalues, eigenvectors = torch.linalg.eigh(stats[4])
            eigenvalues = eigenvalues.clamp_min(0).flip(0)
            cumulative = eigenvalues.cumsum(0) / eigenvalues.sum()
            components = int(torch.searchsorted(cumulative, .95)) + 1
            basis = eigenvectors[:, -components:].float()
            layer_audit = {"lambda": regularization, "validation_relative_mse": error,
                           "lambda_candidates": [{"lambda": -lam, "validation_relative_mse": val} for val, lam in candidates],
                           "pca_95_components": components, "fit_dtype": "FP32 sufficient statistics; FP64 solve/eigendecomposition", "pairs": {}}
            target_cols = target_columns[key].to(args.device)
            for pair_name, indices in pairs.items():
                source_index = indices[key]
                column = source_columns[key][:, source_index].to(args.device)
                unit = SIGNS[layer] * column / column.norm()
                specs, selected, mapped = target_condition(unit, matrix, target_cols)
                for arm, spec in specs.items():
                    conditions.setdefault(pair_name + "_" + arm, {})[key] = spec
                h0, h1 = halves[0] @ unit, halves[1] @ unit
                selected["source_index"] = source_index
                selection.setdefault(pair_name, {})[key] = selected
                mapped_vectors.setdefault(pair_name, {})[key] = mapped.cpu()
                layer_audit["pairs"][pair_name] = {"mapped_gain": float(mapped.norm()),
                    "half_map_cosine": float(torch.nn.functional.cosine_similarity(h0, h1, dim=0)),
                    "half_map_norms": [float(h0.norm()), float(h1.norm())],
                    "natural_pca95_energy_fraction": float((basis.T @ unit).square().sum() / unit.square().sum())}
            mapping_audit[key] = layer_audit
            del x, y, p, docs, vx, vy, vp, stats, matrix, bias, halves, eigenvalues, eigenvectors, basis, target_cols
            print(json.dumps({"phase": "mapping", "layer": layer, "lambda": regularization, "validation_relative_mse": error}), flush=True)
        native, native_audit, native_vectors = native_baselines(target)
        conditions.update(native)
        assert len(conditions) == 19
        for pair_name in mapped_vectors:
            for key, vector in mapped_vectors[pair_name].items():
                selection[pair_name][key]["cosine_to_target_native_direction"] = float(torch.nn.functional.cosine_similarity(vector, native_vectors[key], dim=0))
        bundle = {"hidden_size": target[3]["metadata"]["hidden_size"],
                  "intermediate_size": target[3]["metadata"]["intermediate_size"],
                  "conditions": conditions, "source_pairs": pairs,
                  "target_weight_sha256": target[3]["metadata"]["target_weight_sha256_before"]}
        torch.save(bundle, output / "bundle.pt")
        write_json(output / "conditions.json", {"conditions": list(conditions), "selection": selection,
            "random_sources": pairs, "mapping": mapping_audit, "native_baselines": native_audit,
            "increment_mapping": "M delta only; affine bias is never injected", "dose": 1})
        receipt.update(status="completed", ended_utc=utc(), elapsed_seconds=time.monotonic() - started,
                       files={p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name != "receipt.json"})
    except Exception as error:
        receipt.update(status="failed", ended_utc=utc(), error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        write_json(output / "receipt.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--device", default="cuda:0")
    run(parser.parse_args())
