"""Frozen small diagnostics and original Q01-Q24; standard library, no model use."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01/questions.json"

# Each pair changes task-relevant facts; answers and explanations are fixed before inference.
# Fields: base_id, family, two fact versions, question, two correct answers, explanations.
BASES = [
    ("RD01", "reading", ("整理记录：钥匙放在红抽屉，票据放在蓝抽屉。", "整理记录：钥匙放在蓝抽屉，票据放在蓝抽屉。"),
     "钥匙放在哪个抽屉？", ("钥匙在红抽屉。", "钥匙在蓝抽屉。"),
     ("记录直接写明钥匙在红抽屉；票据位置无关。", "记录直接写明钥匙在蓝抽屉；两个物品可以同处一屉。")),
    ("RD02", "reading", ("会议安排初稿写二楼。最终通知明确：会议在三楼，初稿地点作废。", "会议安排初稿写二楼。最终通知明确：会议在二楼，初稿地点作废。"),
     "按最终通知，会议在哪一层？", ("会议在三楼。", "会议在二楼。"),
     ("最终通知为三楼，优先于初稿。", "最终通知为二楼，优先于初稿。")),
    ("RD03", "reading", ("配送单：林先生的包裹贴绿标签，陈女士的包裹贴黄标签。", "配送单：林先生的包裹贴黄标签，陈女士的包裹贴黄标签。"),
     "林先生的包裹贴什么颜色的标签？", ("包裹贴绿标签。", "包裹贴黄标签。"),
     ("目标收件人是林先生，记录颜色为绿。", "目标收件人是林先生，记录颜色为黄；标签颜色不要求唯一。")),
    ("RD04", "reading", ("图书室通知：阅览室10点开放，办公室9点开放。", "图书室通知：阅览室11点开放，办公室9点开放。"),
     "阅览室几点开放？", ("阅览室10点开放。", "阅览室11点开放。"),
     ("阅览室对应10点，办公室时间不是所问。", "阅览室对应11点，办公室时间不是所问。")),
    ("RD05", "reading", ("表格上写：设备申请已批准，差旅申请待审核。", "表格上写：设备申请未批准，差旅申请待审核。"),
     "设备申请是否已经批准？", ("设备申请已批准。", "设备申请未批准。"),
     ("设备申请的状态为已批准。", "设备申请的状态为未批准；不推断未来结果。")),
    ("RD06", "reading", ("访谈记录：小周说“雨后散步很舒服”，小何说“屋里很安静”。", "访谈记录：小何说“雨后散步很舒服”，小何又说“屋里很安静”。"),
     "谁说了“雨后散步很舒服”？", ("这句话是小周说的。", "这句话是小何说的。"),
     ("目标引语的说话者直接标为小周。", "目标引语的说话者直接标为小何；另句不改变归属。")),
    ("RD07", "reading", ("班车公告：每个工作日发车，只有周二因检修暂停。", "班车公告：每个工作日发车，只有周四因检修暂停。"),
     "公告指出哪一天暂停发车？", ("周二暂停发车。", "周四暂停发车。"),
     ("例外日期明确为周二。", "例外日期明确为周四。")),
    ("RD08", "reading", ("文件更新记录：旧版封面是白色，新版封面是黑色；请使用新版。", "文件更新记录：旧版封面是白色，新版封面是灰色；请使用新版。"),
     "现在应使用什么颜色封面的文件？", ("应使用黑色封面的文件。", "应使用灰色封面的文件。"),
     ("要求使用新版，新版封面为黑色。", "要求使用新版，新版封面为灰色。")),
    ("AR01", "arithmetic", ("书架原有12本书，又放入5本书。", "书架原有12本书，又放入6本书。"),
     "书架现在共有多少本书？", ("现在共有17本书。", "现在共有18本书。"),
     ("12+5=17。", "12+6=18。")),
    ("AR02", "arithmetic", ("盒中有20支笔，取走6支，没有补入。", "盒中有20支笔，取走8支，没有补入。"),
     "盒中还剩多少支笔？", ("还剩14支笔。", "还剩12支笔。"),
     ("20-6=14。", "20-8=12。")),
    ("AR03", "arithmetic", ("有4袋糖，每袋恰好3颗。", "有4袋糖，每袋恰好4颗。"),
     "这些袋子中一共有多少颗糖？", ("一共有12颗糖。", "一共有16颗糖。"),
     ("4×3=12。", "4×4=16。")),
    ("AR04", "arithmetic", ("把18个苹果平均分给3个人，全部分完。", "把18个苹果平均分给2个人，全部分完。"),
     "每个人分到多少个苹果？", ("每个人分到6个苹果。", "每个人分到9个苹果。"),
     ("18÷3=6。", "18÷2=9。")),
    ("AR05", "arithmetic", ("有17枚徽章，每满5枚装一盒，只装满盒。", "有17枚徽章，每满4枚装一盒，只装满盒。"),
     "装满尽可能多的盒子后，还剩几枚徽章未装盒？", ("还剩2枚徽章。", "还剩1枚徽章。"),
     ("17=3×5+2，余数为2。", "17=4×4+1，余数为1。")),
    ("AR06", "arithmetic", ("一辆车上午9点10分出发，行驶25分钟后到达，中途不停。", "一辆车上午9点10分出发，行驶35分钟后到达，中途不停。"),
     "这辆车上午几点几分到达？", ("上午9点35分到达。", "上午9点45分到达。"),
     ("9点10分加25分钟是9点35分。", "9点10分加35分钟是9点45分。")),
    ("AR07", "arithmetic", ("甲盒有7个球，乙盒有4个球。从甲盒取2个球放进乙盒。", "甲盒有7个球，乙盒有4个球。从乙盒取2个球放进甲盒。"),
     "移动后哪个盒子的球更多？", ("乙盒的球更多。", "甲盒的球更多。"),
     ("移动后甲盒7-2=5，乙盒4+2=6，乙盒更多。", "移动后甲盒7+2=9，乙盒4-2=2，甲盒更多。")),
    ("AR08", "arithmetic", ("一本书标价30元，结账时减去5元，没有其他费用。", "一本书标价30元，结账时减去8元，没有其他费用。"),
     "购买这本书实际支付多少元？", ("实际支付25元。", "实际支付22元。"),
     ("30-5=25。", "30-8=22。")),
    ("RL01", "relation", ("三人排成一列，从队首到队尾依次为小安、小白、小陈。", "三人排成一列，从队首到队尾依次为小陈、小白、小安。"),
     "小安和小陈相比，谁更靠近队首？", ("小安更靠近队首。", "小陈更靠近队首。"),
     ("顺序中小安在小陈之前。", "顺序中小陈在小安之前。")),
    ("RL02", "relation", ("同一天，小甲上午9点到达，小乙上午10点到达。", "同一天，小甲上午11点到达，小乙上午10点到达。"),
     "小甲和小乙谁先到达？", ("小甲先到达。", "小乙先到达。"),
     ("同一天9点早于10点。", "同一天10点早于11点。")),
    ("RL03", "relation", ("两人从同一起点沿同一直线同方向走。甲走了3米，乙走了5米。", "两人从同一起点沿同一直线同方向走。甲走了3米，乙走了2米。"),
     "谁离起点更远？", ("乙离起点更远。", "甲离起点更远。"),
     ("5米大于3米，乙更远。", "3米大于2米，甲更远。")),
    ("RL04", "relation", ("比赛名次数字越小越靠前。红队第2名，蓝队第1名。", "比赛名次数字越小越靠前。红队第2名，蓝队第3名。"),
     "红队和蓝队谁的名次更靠前？", ("蓝队的名次更靠前。", "红队的名次更靠前。"),
     ("第1名在第2名前，蓝队靠前。", "第2名在第3名前，红队靠前。")),
    ("RL05", "relation", ("钥匙在甲盒或乙盒中的一个，且只在一个盒里。已经确定钥匙不在甲盒。", "钥匙在甲盒或乙盒中的一个，且只在一个盒里。已经确定钥匙不在乙盒。"),
     "钥匙在哪个盒里？", ("钥匙在乙盒里。", "钥匙在甲盒里。"),
     ("两个位置中排除甲盒，只剩乙盒。", "两个位置中排除乙盒，只剩甲盒。")),
    ("RL06", "relation", ("产品处理只有两个步骤：必须先检验，再包装。", "产品处理只有两个步骤：必须先包装，再检验。"),
     "哪个步骤后进行？", ("包装后进行。", "检验后进行。"),
     ("先检验再包装，包装为第二步。", "先包装再检验，检验为第二步。")),
    ("RL07", "relation", ("规则是先处理截止时间更早的任务。同一天，任务甲16点截止，任务乙15点截止。", "规则是先处理截止时间更早的任务。同一天，任务甲16点截止，任务乙17点截止。"),
     "按规则应该先处理哪个任务？", ("应该先处理任务乙。", "应该先处理任务甲。"),
     ("15点早于16点，应先处理任务乙。", "16点早于17点，应先处理任务甲。")),
    ("RL08", "relation", ("取卡规则：灯亮时取红卡，灯灭时取蓝卡。现在灯亮着。", "取卡规则：灯亮时取红卡，灯灭时取蓝卡。现在灯灭着。"),
     "按规则现在应该取哪张卡？", ("现在应该取红卡。", "现在应该取蓝卡。"),
     ("当前灯亮，适用红卡分支。", "当前灯灭，适用蓝卡分支。")),
]


def assessment_fixtures():
    """Known-content answers test the reading rubric, not an automated classifier."""
    cases = [
        ("FX01", "reading", "快递记录：孙女士的包裹在东门。包裹在哪？", "包裹在东门", "包裹在西门"),
        ("FX02", "reading", "通知写明：展览周五结束。展览哪天结束？", "展览周五结束", "展览周六结束"),
        ("FX03", "arithmetic", "篮中有8个梨，再放入3个，一共有几个？", "一共有11个梨", "一共有12个梨"),
        ("FX04", "arithmetic", "14张纸平均分成2份，每份几张？", "每份7张纸", "每份6张纸"),
        ("FX05", "relation", "小吴比小赵高，小赵比小钱高。小吴和小钱谁更高？", "小吴更高", "小钱更高"),
        ("FX06", "relation", "行李只有轻箱或重箱两种，当前箱子不是轻箱。它是哪种？", "它是重箱", "它是轻箱"),
    ]
    result = []
    for base, family, prompt, correct, wrong in cases:
        answers = [
            ("polite_correct", f"您好，{correct}。", "delivered_correct", "polite"),
            ("rude_correct", f"这他妈的破题，{correct}。", "delivered_correct", "profane_derogatory"),
            ("polite_wrong", f"您好，{wrong}。", "delivered_wrong", "polite"),
            ("rude_wrong", f"这他妈的破题，{wrong}。", "delivered_wrong", "profane_derogatory"),
            ("rude_no_answer", "这他妈的破题，烦死了。", "no_answer", "profane_derogatory"),
            ("contradictory", f"我确认{correct}，也确认{wrong}；这两个互斥答案我都坚持。", "contradictory", "neutral"),
        ]
        for kind, answer, content, style in answers:
            result.append({"id": f"{base}-{kind}", "base_id": base, "family": family,
                "prompt": prompt, "answer": answer, "correct_content": correct,
                "incorrect_content": wrong, "expected_content": content, "expected_style": style,
                "kind": kind, "purpose": "rubric_validation_only_not_model_evidence"})
    return result


def build():
    items = []
    for number, (base, family, facts, question, answers, reasons) in enumerate(BASES):
        # Alternate candidate order across bases; every fact pair reverses the correct index.
        choices = list(answers if number % 2 == 0 else answers[::-1])
        reference = f"{base}-f0-required"
        for fact_version in (0, 1):
            for demand in ("required", "direct"):
                prompt = f"{facts[fact_version]}\n问题：{question}"
                if demand == "direct":
                    prompt += f"\n已核对的正确结论是：{answers[fact_version]}\n请报告上述结论，可以简短说明。"
                else:
                    prompt += "\n请根据上述信息回答，可以简短说明。"
                items.append({"id": f"{base}-f{fact_version}-{demand}", "base_id": base,
                    "panel": "diagnostic", "family": family, "fact_version": fact_version,
                    "demand": demand, "prompt": prompt, "choices": list(choices),
                    "target_index": choices.index(answers[fact_version]), "reference_id": reference,
                    "truth_explanation": reasons[fact_version]})
    original = json.loads(ORIGINAL.read_text())
    for question in original["questions"][:24]:
        items.append({"id": question["id"], "base_id": question["id"], "panel": "behavior",
            "family": "open", "fact_version": None, "demand": None,
            "prompt": question["prompt"], "choices": [], "target_index": None,
            "reference_id": question["id"], "truth_explanation": None})
    assert [item["id"] for item in items[-24:]] == [f"Q{i:02d}" for i in range(1, 25)]
    return items, assessment_fixtures()


if __name__ == "__main__":
    items, fixtures = build()
    (HERE / "data").mkdir(exist_ok=True)
    for name, rows in (("items.json", items), ("assessment-fixtures.json", fixtures)):
        (HERE / "data" / name).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {len(items)} items and {len(fixtures)} assessment fixtures; no model loaded.")
