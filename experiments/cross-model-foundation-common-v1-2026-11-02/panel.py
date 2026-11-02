"""Deterministic English input panel (PLAN r3 §3).

36 base scenarios: 12 dev, 12 analysis, 12 lock; 4 per task family per split.
Families: ea (entity-attribute), id (record code lookup), num (numeric value).
Each scenario has two fact versions f0/f1 that swap the asked value between the
target row and one distractor row, so both candidates appear in the records in
both versions and the correct candidate flips.  The lock split uses different,
pre-written wording.  Nothing here depends on any model output.
"""
import hashlib
import json
import random
import re

SEED = 20261102
SPLITS = ("dev", "analysis", "lock")
FAMILIES = ("ea", "id", "num")
N_ROWS = 7

FIRST = ["Talvin", "Morra", "Quessa", "Dovric", "Ylna", "Bressa", "Kortan", "Velim", "Asharo", "Nibbel",
         "Fenric", "Olvae", "Tamsin", "Gorlek", "Pellan", "Ruvia", "Sorcan", "Ithel", "Wenna", "Jorvik",
         "Caddis", "Elmar", "Harlo", "Ziven"]
LAST = ["Osk", "Tarrow", "Vell", "Brinmoor", "Quill", "Dask", "Ferral", "Lune", "Mardek", "Pell",
        "Corvan", "Hessle", "Ivory", "Kesk", "Ondra", "Ruel", "Sallow", "Tirn", "Varga", "Wick"]
PLACES = ["Brelton", "Cassmere", "Dunvale", "Esk Ford", "Farrowgate", "Glimmock", "Hollin", "Istry",
          "Jarrow Pike", "Kelmouth", "Lornhaven", "Mistle", "Norrow", "Ostwick", "Pellbrook", "Quarrin"]
COLORS = ["amber", "cobalt", "crimson", "olive", "violet", "silver", "teal", "ochre", "ivory", "maroon",
          "coral", "indigo", "copper", "jade", "scarlet", "beige"]
LETTERS = "BCDFGHJKLMNPRSTVWXZ"

TEMPLATES = {
    "main": {
        "row_id": "R{k}",
        "intro": "Here are some records.",
        "ea_row": "{rid} | name: {name} | color: {color} | badge: {badge}",
        "id_row": "{rid} | owner: {name} | code: {code}",
        "num_row": "{rid} | depot: {place} | crates: {crates} | trucks: {trucks}",
        "ea_q": "What color is listed for {name}?",
        "id_q": "Which code belongs to the owner {name}?",
        "num_q": "How many crates are listed for the {place} depot?",
        "a_instr": "Answer with exactly one of these two options: {c1} or {c2}. Reply with the option only.",
        "b_instr": "First give the record identifier, then the answer, in the form: <identifier>: <answer>.",
        "q_prefix": "Question: ",
    },
    "lock": {
        "row_id": "E{k}",
        "intro": "Read the entries below.",
        "ea_row": "Entry {rid}: {name}; colour on file is {color}; badge number {badge}",
        "id_row": "Entry {rid}: held by {name}; code on file is {code}",
        "num_row": "Entry {rid}: the {place} depot holds {crates} crates and {trucks} trucks",
        "ea_q": "Which colour is on file for {name}?",
        "id_q": "What code is on file for the holder {name}?",
        "num_q": "What number of crates does the {place} depot hold?",
        "a_instr": "Choose one option, {c1} or {c2}, and write only that option.",
        "b_instr": "Start with the entry identifier, then give the answer, formatted as <identifier>: <answer>.",
        "q_prefix": "",
    },
}


def _rng(*parts):
    return random.Random("|".join(str(p) for p in (SEED,) + parts))


def _rows_for(family, rng):
    names = rng.sample([f"{a} {b}" for a in FIRST for b in LAST], N_ROWS)
    if family == "ea":
        colors = rng.sample(COLORS, N_ROWS)
        badges = rng.sample(range(10, 99), N_ROWS)
        return [{"name": n, "color": c, "badge": str(b)} for n, c, b in zip(names, colors, badges)], "color", "name"
    if family == "id":
        codes = set()
        while len(codes) < N_ROWS:
            codes.add(f"{rng.choice(LETTERS)}-{rng.randint(100, 999)}")
        codes = rng.sample(sorted(codes), N_ROWS)
        return [{"name": n, "code": c} for n, c in zip(names, codes)], "code", "name"
    places = rng.sample(PLACES, N_ROWS)
    crates = rng.sample(range(10, 99), N_ROWS)
    trucks = [str(rng.randint(1, 9)) for _ in range(N_ROWS)]
    return [{"place": p, "crates": str(c), "trucks": t} for p, c, t in zip(places, crates, trucks)], "crates", "place"


def _scenario(split, family, idx):
    rng = _rng(split, family, idx)
    rows, asked, key = _rows_for(family, rng)
    target, distractor = rng.sample(range(N_ROWS), 2)
    # Candidate listing order balanced: alternate by index within split/family.
    target_first = (idx % 2 == 0)
    return {"split": split, "family": family, "index": idx,
            "id": f"{split[:3].upper()}-{family}-{idx:02d}",
            "rows": rows, "asked": asked, "key": key,
            "target_row": target, "distractor_row": distractor,
            "target_listed_first": target_first}


def _fact_rows(sc, fact):
    rows = [dict(r) for r in sc["rows"]]
    if fact == 1:
        t, d, a = sc["target_row"], sc["distractor_row"], sc["asked"]
        rows[t][a], rows[d][a] = rows[d][a], rows[t][a]
    return rows


def render_item(sc, fact, task):
    """Return the user message text plus metadata for one (scenario, fact, task) item."""
    assert task in ("A", "B") and fact in (0, 1)
    tpl = TEMPLATES["lock" if sc["split"] == "lock" else "main"]
    rows = _fact_rows(sc, fact)
    fam = sc["family"]
    lines = []
    for k, r in enumerate(rows, start=1):
        rid = tpl["row_id"].format(k=k)
        lines.append(tpl[f"{fam}_row"].format(rid=rid, **r))
    record_block = "\n".join(lines)
    t, d = sc["target_row"], sc["distractor_row"]
    keyval = rows[t][sc["key"]]
    question = tpl["q_prefix"] + tpl[f"{fam}_q"].format(**{sc["key"]: keyval})
    correct = rows[t][sc["asked"]]
    other = rows[d][sc["asked"]]
    if task == "A":
        c1, c2 = (correct, other) if (sc["target_listed_first"] ^ (fact == 1)) else (other, correct)
        instr = tpl["a_instr"].format(c1=c1, c2=c2)
    else:
        c1 = c2 = None
        instr = tpl["b_instr"]
    head = tpl["intro"] + "\n\n"
    user = head + record_block + "\n\n" + question + "\n" + instr
    start = len(head)
    assert user[start:start + len(record_block)] == record_block
    return {"item_id": f"{sc['id']}-f{fact}-{task}", "scenario_id": sc["id"], "split": sc["split"],
            "family": fam, "fact": fact, "task": task, "user": user,
            "record_char_span": [start, start + len(record_block)],
            "correct": correct, "other": other,
            "candidates_in_order": [c1, c2] if task == "A" else None,
            "target_row_id": tpl["row_id"].format(k=t + 1),
            "row_ids": [tpl["row_id"].format(k=k) for k in range(1, N_ROWS + 1)],
            "column_values": [r[sc["asked"]] for r in rows],
            "row_id_pattern": r"\b" + tpl["row_id"][0] + r"(\d+)\b"}


def scenarios():
    return [_scenario(s, f, i) for s in SPLITS for f in FAMILIES for i in range(4)]


def items(task):
    return [render_item(sc, fact, task) for sc in scenarios() for fact in (0, 1)]


def panel_sha256():
    blob = json.dumps({"A": items("A"), "B": items("B")}, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()


# ---------- B parser (PLAN r3 §6: mechanical, no LLM judge) ----------

def parse_b(item, text):
    """Classify a free-generation answer.  Returns (label, delivered: bool or None).

    delivered=None marks unscorable (handled by worst-case bounds in analysis).
    """
    values = item["column_values"]
    found = []
    for v in set(values):
        for m in re.finditer(r"(?<![\w-])" + re.escape(v) + r"(?![\w-])", text):
            found.append((m.start(), v))
    found.sort()
    ids = [(m.start(), m.group(0)) for m in re.finditer(item["row_id_pattern"], text)]
    mentioned = {v for _, v in found}
    if not mentioned:
        return "no_answer", False
    if mentioned == {item["correct"]}:
        first_id = ids[0][1] if ids else None
        if first_id == item["target_row_id"]:
            return "correct", True
        return ("value_right_id_missing" if first_id is None else "value_right_id_wrong"), False
    if item["correct"] in mentioned:
        return "conflict", None
    return "wrong_value", False
