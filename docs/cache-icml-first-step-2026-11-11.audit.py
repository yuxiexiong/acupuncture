"""Check cited summaries against archived JSON; no model calls or new statistics."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "spf": "experiments/cache-selection-precedence-v1-2026-11-06/analysis/spf-readouts-A-r01.json",
    "dwb": "experiments/cache-donor-write-bridge-v2-2026-11-07/analysis/dwb-readouts-formal-r02.json",
    "dwc": "experiments/cache-write-read-confirm-v1-2026-11-07/analysis/dwc-readouts-formal-r01.json",
    "ngc": "experiments/cache-native-gain-v1-2026-11-08/runs/formal-20261111-r01/analysis.json",
}


def main():
    data = {name: json.loads((ROOT / path).read_text()) for name, path in SOURCES.items()}
    checks = []

    def check(source, path, expected, tolerance=0.00051):
        actual = data[source]
        for key in path:
            actual = actual[key]
        passed = abs(actual - expected) <= tolerance
        checks.append(dict(source=SOURCES[source], keys=path, actual=actual,
                           expected=expected, tolerance=tolerance, passed=passed))
        if not passed:
            raise ValueError(checks[-1])

    a, b = "N_L00_C4146_D-1", "N_L00_C1210_D-1"
    for cell, value in zip("abcd", [0, 0, 0, 0.896]):
        check("spf", ["directions", a, "decision", "D", cell, "mean"], value)
    for direction, values in [(a, [0.882, 0, 0.094]), (b, [0.427, 0, 0.799])]:
        for arm, value in zip(["DO", "OD", "CSTd"], values):
            check("dwb", ["directions", direction, "decision", "D", arm, "mean"], value)
    for direction, values in [(a, [0.311, 0.473, 0.394]), (b, [0.213, 0.294, 0.322])]:
        for metric, value in zip(["G", "W", "R"], values):
            check("dwc", ["directions", direction, "uses", "D", metric, "mean"], value)
    check("dwc", ["directions", b, "uses", "D", "G", "hi"], 0.234)
    families = {}
    for direction, values in [(a, [0.117, 0.352, 0.502, 0.372, 0.156, 0.367]),
                              (b, [0.208, 0.139, 0.030, 0.301, 0.409, 0.189])]:
        families[direction] = data["dwc"]["directions"][direction]["uses"]["D"]["G"]["by_family"]
        for family, value in zip([f"NQ{i:02d}" for i in range(1, 7)], values):
            check("dwc", ["directions", direction, "uses", "D", "G", "by_family", family], value)
    ngc_counts = {}
    for direction, expected in [(a, (0, 0)), (b, (1, 1)),
                                ("R0_L00_D-1", (1, 0)), ("N_L00_C1343_D-1", (0, 0))]:
        d = data["ngc"]["directions"][direction]
        for arm, value in zip([direction, "T-P|" + direction], expected):
            check("ngc", ["directions", direction, "arms", arm, "correct"], value, 0)
        if d["recovery"]["fixed"]:
            raise ValueError("Unexpected repaired answers: " + direction)
        ngc_counts[direction] = {"native": expected[0], "adjusted": expected[1],
                                 "repaired": len(d["recovery"]["fixed"])}
    source_paths = list(SOURCES.values()) + [
        "experiments/cache-selection-precedence-v1-2026-11-06/CONTRACT.zh-CN.md",
        "experiments/cache-selection-precedence-v1-2026-11-06/REPORT.zh-CN.md",
        "experiments/cache-donor-write-bridge-v2-2026-11-07/CONTRACT.zh-CN.md",
        "experiments/cache-donor-write-bridge-v2-2026-11-07/REPORT.zh-CN.md",
        "experiments/cache-write-read-confirm-v1-2026-11-07/CONTRACT.zh-CN.md",
        "experiments/cache-write-factor-audit-2026-11-08/READOUT.zh-CN.md",
        "experiments/cache-native-gain-v1-2026-11-08/REPORT.zh-CN.md",
        "experiments/layer-trace-extension-v1-2026-10-28/analysis-early-r01/REPORT.zh-CN.md",
        "docs/mechanism-paper-evidence-gaps-2026-11-06.zh-CN.md",
        "docs/cache-mechanism-p1-judgment-2026-11-08.zh-CN.md",
    ]
    result = {
        "status": "passed", "scope": "summary extraction and cited-number checks, not raw-output reproduction",
        "model_calls": 0, "gpu_hours": 0, "checks": checks,
        "DWC_G_D_all_families": families, "NGC_complete_answer_counts": ngc_counts,
        "sources": [{"path": p, "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
                    for p in source_paths],
    }
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Passed {len(checks)} cited-number checks; {len(source_paths)} source hashes; {output.name}")


if __name__ == "__main__":
    main()
