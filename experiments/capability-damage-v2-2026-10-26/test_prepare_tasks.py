"""CPU checks for preserving common contexts, delimiters, and immutable frozen files."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from prepare_tasks import export_task, save_once


class Task:
    config = SimpleNamespace(task="mmlu_test", dataset_name="test")
    OUTPUT_TYPE = "multiple_choice"
    doc = {"answer": 1}
    eval_docs = [doc]

    def __init__(self):
        self.instances = [SimpleNamespace(doc_id=0, idx=i, doc=self.doc, args=("Question?\nAnswer:", " " + letter))
                          for i, letter in enumerate("ABCD")]

    def build_all_requests(self, **kwargs):
        assert kwargs == {"cache_requests": False, "apply_chat_template": False}

    def doc_to_target(self, doc):
        return doc["answer"]

    def doc_to_choice(self, doc):
        return list("ABCD")


task = Task()
row, = export_task("mmlu", task, set())
assert row["choices"] == ["A", "B", "C", "D"]
assert row["continuations"] == [" A", " B", " C", " D"]
assert row["context"] == "Question?\nAnswer:" and row["target_index"] == 1
task.instances[-1].args = ("Candidate-specific context must fail", " D")
try:
    export_task("mmlu", task, set())
except AssertionError:
    pass
else:
    raise AssertionError("Different candidate calibration contexts were accepted")

with TemporaryDirectory() as directory:
    path = Path(directory) / "frozen.json"
    save_once(path, b"same")
    save_once(path, b"same")
    try:
        save_once(path, b"different")
    except AssertionError:
        pass
    else:
        raise AssertionError("Changed frozen artifact was overwritten")
    assert path.read_bytes() == b"same"

print("PASS: exact continuations, common calibration context, immutable frozen output")
