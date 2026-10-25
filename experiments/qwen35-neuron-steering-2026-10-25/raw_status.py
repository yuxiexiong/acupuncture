"""Print collection progress and technical status without printing response text."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

root = Path(sys.argv[1])
receipt = json.loads((root / "receipt.json").read_text())
status = {
    "status": receipt["status"],
    "completed_pairs": len(receipt["completed_questions"]),
    "expected_pairs": len(receipt["expected_question_ids"]),
    "current_question": receipt.get("current_question"),
    "elapsed_minutes": round((datetime.now(timezone.utc) - datetime.fromisoformat(receipt["started_utc"])).total_seconds() / 60, 1),
}
if receipt.get("error"):
    status["error"] = receipt["error"]
if receipt.get("current_question"):
    record = json.loads((root / (receipt["current_question"] + ".json")).read_text())
    status["current_attempts"] = [
        {"budget": attempt["max_new_tokens"], **{arm: attempt[arm]["status"] for arm in ("baseline", "modified")}}
        for attempt in record["attempts"]
    ]
exit_path = root.parent / "raw40.exit"
status["launcher_exit"] = exit_path.read_text().strip() if exit_path.exists() else None
print(json.dumps(status, ensure_ascii=False))
