from scoring_crosscheck import author_gsm_answer, explicit_answer


def parse(text, benchmark="race"):
    return explicit_answer(text, benchmark)["parsed"]


assert parse("A rich man went home.") is None
assert parse("A. rich man went home.") is None
assert parse("The answer is correct.") is None
assert parse("The answer is a rich man.") is None
assert parse("The answer is A or B.") is None
assert parse("Answer: A, B.") is None
assert parse("The answer is A, or B.") is None
assert parse("The correct answer is **C**.\nExplanation mentions A, B and D.") == "C"
assert parse("**C**\nThe other options A, B and D are wrong.") == "C"
assert parse("(b)\nExplanation") == "B"
assert parse("C\nThe final answer is D.") is None
assert parse("Answer: A. The final answer is B.") is None
assert parse("Answer: C. The final answer is C.") == "C"
assert parse("Options A and C are mentioned, but no answer is selected.") is None
assert parse("#### 1,200.00", "gsm8k") == "1200"
assert parse(r"\boxed{1200} and here is an explanation", "gsm8k") is None
assert parse(r"\boxed{1200}.", "gsm8k") == "1200"
assert parse("The final answer is **1,200.00**.", "gsm8k") == "1200"
assert parse("#### 1200\nThe final answer is 1200.0.", "gsm8k") == "1200"
assert parse("#### 1200\nThe final answer is 12.", "gsm8k") is None
assert parse("We have 2 apples and 3 oranges, making 5.", "gsm8k") is None
for value in ("1/2", "1e3", "1,23", "1.2.3", "1 + 2", "1 or 2"):
    assert parse("The final answer is " + value, "gsm8k") is None, value
assert parse("-0.0", "gsm8k") == "0"
for currency in "$£€¥₹₩₽":
    assert parse("#### " + currency + " 1,234.50", "gsm8k") == "1234.5"
    assert parse("Final answer: " + currency + "20.00.", "gsm8k") == "20"
    assert parse("\\boxed{" + currency + "20.00}", "gsm8k") == "20"
    assert parse(currency + "20.00", "gsm8k") == "20"
    assert parse("I bought " + currency + "20 of goods.", "gsm8k") is None
assert parse("#### $20\nFinal answer: €21", "gsm8k") is None
assert parse("Final answer: $1/2", "gsm8k") is None
assert author_gsm_answer("#### 1,200.0\n#### 12") == "1200.0"
assert author_gsm_answer("1200") is None
assert author_gsm_answer("#### 1.0") != author_gsm_answer("#### 1")
print("PASS: explicit-only, Markdown, distractors, conflicts, numeric boundaries, and separate author regex")
