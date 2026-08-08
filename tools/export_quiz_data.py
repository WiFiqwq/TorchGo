import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT / "apps" / "desktop"
WWW = ROOT / "apps" / "android" / "www"
sys.path.insert(0, str(DESKTOP))

from applied_questions import APPLIED_QUESTIONS  # noqa: E402
from pytorch_quiz import CATEGORY_TO_CHAPTER, CHAPTERS, KNOWLEDGE  # noqa: E402


WWW.mkdir(parents=True, exist_ok=True)
payload = {
    "chapters": CHAPTERS,
    "categoryToChapter": CATEGORY_TO_CHAPTER,
    "knowledge": KNOWLEDGE,
    "applied": APPLIED_QUESTIONS,
}
(WWW / "data.js").write_text(
    "window.QUIZ_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
    encoding="utf-8",
)
print(f"Exported {len(KNOWLEDGE)} knowledge cards and {len(APPLIED_QUESTIONS)} applied questions")
