"""Frozen output classes and answer rubric for DIV-01 threshold-split survey."""
import re

GRADED = ("Q01", "Q02", "Q04", "Q07", "Q08")


def output_class(o):
    t, n = o["token_ids"], o["generated_token_count"]
    if o["end_reason"] == "eos_token" and n <= 2:
        return "EOS"
    if len(set(t[:40])) <= 3:
        return "COLLAPSE"
    if o["end_reason"] == "eos_token":
        return "TEXT"
    return "LONG"  # hit 128-token limit without collapsing


def answer_ok(qid, text):
    s = text.replace(" ", "")
    if qid == "Q01":
        return bool(re.search(r"不能|无法|不可以|进不去", s)) and not re.search(r"(?<!不)(?<!无法)能进去借书。", s)
    if qid == "Q02":
        return bool(re.search(r"一样多|相同|相等|同样多", s))
    if qid == "Q04":
        return "第一步：" in s and "第二步：" in s and len([l for l in text.splitlines() if l.strip()]) == 2
    if qid == "Q07":
        return bool(re.search(r"无法|不能确定|不确定|查询|查看|不知道|取决于", s))
    if qid == "Q08":
        return bool(re.search(r"不对|错误|不正确|不准确", s)) and ("365" in s)
    return None


def record_label(o, qid):
    c = output_class(o)
    if c not in ("TEXT", "LONG"):
        return c  # EOS / COLLAPSE; truncated non-collapsed text is graded like text
    ok = answer_ok(qid, o["answer_text"])
    return "TEXT" if ok is None else ("OK" if ok else "WRONG")


def channel_role(labels):
    """labels: dict qid->label for 8 questions at one dose."""
    eos = sum(v == "EOS" for v in labels.values())
    if eos >= 6:
        return "STOP"
    if all(v in ("OK", "TEXT") for v in labels.values()):
        return "CLEAN"
    return "OTHER"
