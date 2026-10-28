"""Prepare fixed development, unopened confirmation, and historical anchor inputs."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JOINT = ROOT / "experiments/joint-behavior-capability-v1-2026-10-28/data/items.json"
SURVEY = ROOT / "experiments/layer-survey-toy-v1-2026-10-27"
DEVELOPMENT_BASES = tuple(f"{family}{i:02d}" for family in ("RD", "AR", "RL") for i in range(1, 5))

# New structures, not renamed copies of the old single-operation diagnostics.
# Each entry fixes two facts, a question, the corresponding answers, and reasons.
CONFIRMATION_BASES = [
    ("CRD01", "reading", "table_row_and_column",
     ("登记表的三列依次为编号、入库日、状态。两行记录是：甲｜周一｜待检；乙｜周二｜已检。",
      "登记表的三列依次为编号、入库日、状态。两行记录是：甲｜周一｜待检；乙｜周三｜已检。"),
     "编号乙的入库日是哪一天？", ("入库日是周二。", "入库日是周三。"),
     ("按编号乙定位第二行，再取入库日列，值为周二。",
      "按编号乙定位第二行，再取入库日列，值为周三。")),
    ("CRD02", "reading", "annotation_scope",
     ("便条约定：〔〕内是已确认信息，（）内是待核对信息。便条内容为：〔备用电池在左柜〕（备用电池在右柜）。",
      "便条约定：〔〕内是已确认信息，（）内是待核对信息。便条内容为：〔备用电池在右柜〕（备用电池在右柜）。"),
     "已确认的备用电池位置在哪里？", ("已确认的位置是左柜。", "已确认的位置是右柜。"),
     ("只读取〔〕中的已确认信息，位置为左柜；括号中的右柜尚待核对。",
      "〔〕中的已确认位置为右柜；另一条也写右柜不改变其证据范围。")),
    ("CRD03", "reading", "directed_transfer_record",
     ("交接记录中，箭头左边是交出方，右边是接收方。记录为：小林→小何：资料袋；小何→小周：工具袋。",
      "交接记录中，箭头左边是交出方，右边是接收方。记录为：小林→小周：资料袋；小何→小周：工具袋。"),
     "资料袋的接收方是谁？", ("资料袋由小何接收。", "资料袋由小周接收。"),
     ("资料袋对应第一条记录，箭头右侧为小何；第二条记录的物品不同。",
      "资料袋对应第一条记录，箭头右侧为小周；两件物品可以由同一人接收。")),
    ("CRD04", "reading", "former_latter_reference",
     ("记录写道：桌上有一个纸盒和一个布袋；前者装票根，后者装钥匙。",
      "记录写道：桌上有一个纸盒和一个布袋；前者装票根，后者装印章。"),
     "布袋里装的是什么？", ("布袋里装的是钥匙。", "布袋里装的是印章。"),
     ("布袋是后提到的物品，后者指布袋，所装物为钥匙。",
      "布袋是后提到的物品，后者指布袋，所装物为印章。")),
    ("CAR01", "arithmetic", "reverse_two_operations",
     ("一张储值卡先支出5元，随后收入2元，最后余额为14元。期间没有其他收支。",
      "一张储值卡先支出5元，随后收入2元，最后余额为15元。期间没有其他收支。"),
     "这张卡最初的余额是多少元？", ("最初余额是17元。", "最初余额是18元。"),
     ("设最初余额为x，x-5+2=14，所以x=14-2+5=17。",
      "设最初余额为x，x-5+2=15，所以x=15-2+5=18。")),
    ("CAR02", "arithmetic", "proportion_scaling",
     ("配方要求水和粉始终保持同一比例：每4毫升水配6克粉。这次用了8毫升水。",
      "配方要求水和粉始终保持同一比例：每4毫升水配6克粉。这次用了12毫升水。"),
     "按配方应该配多少克粉？", ("应该配12克粉。", "应该配18克粉。"),
     ("8毫升是4毫升的2倍，所需粉为6×2=12克。",
      "12毫升是4毫升的3倍，所需粉为6×3=18克。")),
    ("CAR03", "arithmetic", "arithmetic_mean",
     ("某物体两次称重分别为14克和18克。记录值规定为这两次数值的算术平均数。",
      "某物体两次称重分别为14克和22克。记录值规定为这两次数值的算术平均数。"),
     "应记录多少克？", ("应记录16克。", "应记录18克。"),
     ("算术平均数为(14+18)÷2=16克。", "算术平均数为(14+22)÷2=18克。")),
    ("CAR04", "arithmetic", "unknown_count_from_total",
     ("成人票每张8元，儿童票每张5元，没有折扣或其他费用。买了2张成人票和若干张儿童票，总价31元。",
      "成人票每张8元，儿童票每张5元，没有折扣或其他费用。买了2张成人票和若干张儿童票，总价36元。"),
     "买了几张儿童票？", ("买了3张儿童票。", "买了4张儿童票。"),
     ("成人票共2×8=16元，儿童票张数为(31-16)÷5=3。",
      "成人票共2×8=16元，儿童票张数为(36-16)÷5=4。")),
    ("CRL01", "relation", "nested_containment",
     ("盒乙装在箱甲里，袋丙装在盒乙里。箱甲与箱丁是两个互不包含的箱子。",
      "盒乙装在箱丁里，袋丙装在盒乙里。箱甲与箱丁是两个互不包含的箱子。"),
     "袋丙最终位于哪个箱子里面？", ("袋丙位于箱甲里面。", "袋丙位于箱丁里面。"),
     ("袋丙在盒乙中，盒乙在箱甲中，因此袋丙在箱甲中。",
      "袋丙在盒乙中，盒乙在箱丁中，因此袋丙在箱丁中。")),
    ("CRL02", "relation", "spatial_relation_chain",
     ("红点、绿点和蓝点位于同一条水平线上，三个点互不重合。红点在绿点和蓝点之间，绿点在红点左边。",
      "红点、绿点和蓝点位于同一条水平线上，三个点互不重合。红点在绿点和蓝点之间，绿点在红点右边。"),
     "绿点和蓝点相比，哪个更靠左？", ("绿点更靠左。", "蓝点更靠左。"),
     ("从左到右为绿、红、蓝，因此绿点比蓝点更靠左。",
      "红点在绿点与蓝点之间，绿点在红点右边，故从左到右为蓝、红、绿，蓝点更靠左。")),
    ("CRL03", "relation", "category_rule_composition",
     ("分类规则规定：所有铜牌都属于金属类；所有金属类物品一律放进甲柜。每件物品只放一个柜子。",
      "分类规则规定：所有铜牌都属于金属类；所有金属类物品一律放进乙柜。每件物品只放一个柜子。"),
     "按这些规则，一枚铜牌应该放进哪个柜子？", ("铜牌应该放进甲柜。", "铜牌应该放进乙柜。"),
     ("铜牌属于金属类，金属类统一进入甲柜，所以铜牌进入甲柜。",
      "铜牌属于金属类，金属类统一进入乙柜，所以铜牌进入乙柜。")),
    ("CRL04", "relation", "equality_then_comparison",
     ("甲绳与乙绳长度相等，乙绳比丙绳长。", "甲绳与乙绳长度相等，乙绳比丙绳短。"),
     "甲绳和丙绳相比，哪根更长？", ("甲绳更长。", "丙绳更长。"),
     ("甲绳等长于乙绳，乙绳长于丙绳，因此甲绳长于丙绳。",
      "甲绳等长于乙绳，乙绳短于丙绳，因此丙绳长于甲绳。")),
]


def source(path):
    return {"path": str(path.relative_to(ROOT)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build():
    original = json.loads(JOINT.read_text(encoding="utf-8"))
    development = [dict(row, split="development", source=source(JOINT))
                   for row in original
                   if row["base_id"] in DEVELOPMENT_BASES and row["demand"] == "required"]
    confirmation = []
    for number, (base, family, structure, facts, question, answers, reasons) in enumerate(CONFIRMATION_BASES):
        choices = list(answers if number % 2 == 0 else answers[::-1])
        for fact in (0, 1):
            confirmation.append({
                "id": f"{base}-f{fact}-required", "base_id": base,
                "panel": "diagnostic", "family": family, "fact_version": fact,
                "demand": "required", "prompt": f"{facts[fact]}\n问题：{question}\n请根据上述信息回答，可以简短说明。",
                "choices": choices.copy(), "target_index": choices.index(answers[fact]),
                "reference_id": f"{base}-f0-required", "truth_explanation": reasons[fact],
                "split": "confirmation", "source": {"kind": "new_predeclared", "structure": structure},
            })
    questions = json.loads((SURVEY / "questions.json").read_text(encoding="utf-8"))
    instruction = json.loads((SURVEY / "contract.json").read_text(encoding="utf-8"))["instruction"]
    anchors = [{"id": q["id"], "base_id": q["id"], "panel": "anchor", "family": "open",
                "fact_version": None, "demand": None, "prompt": q["prompt"], "choices": [],
                "target_index": None, "reference_id": q["id"], "truth_explanation": None,
                "instruction": instruction, "user_message": instruction + "\n\n" + q["prompt"],
                "split": "anchors", "source": {"questions": source(SURVEY / "questions.json"),
                                                  "contract": source(SURVEY / "contract.json")}}
               for q in questions]
    return {"development": development, "confirmation": confirmation, "anchors": anchors}


def prepare(directory=HERE / "data"):
    directory = Path(directory)
    documents = {directory / f"{name}.json": json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
                 for name, rows in build().items()}
    for path, text in documents.items():
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise ValueError(f"Refusing to overwrite different task data: {path}")
    directory.mkdir(parents=True, exist_ok=True)
    for path, text in documents.items():
        if not path.exists():
            path.write_text(text, encoding="utf-8")
    return {name: len(rows) for name, rows in build().items()}


if __name__ == "__main__":
    if sys.argv[1:] != ["prepare"]:
        raise SystemExit("Usage: python task_data.py prepare")
    print(json.dumps(prepare(), ensure_ascii=False))
