import json
import random
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

from applied_questions import APPLIED_QUESTIONS
from pytorch_quiz import CATEGORY_TO_CHAPTER, CHAPTERS, KNOWLEDGE


APP_DIR = Path(__file__).resolve().parent
PROGRESS_FILE = APP_DIR / "选择题答题记录.json"
STUDY_PROGRESS_FILE = APP_DIR / "学习模式记录.json"
UNFINISHED_EXAM_FILE = APP_DIR / "未完成考试.json"
HISTORY_FILE = APP_DIR / "考试历史.json"

COLORS = {
    "bg": "#F3F6FB", "card": "#FFFFFF", "ink": "#172033",
    "muted": "#667085", "primary": "#3457D5", "primary_dark": "#2947B7",
    "green": "#16865C", "green_soft": "#EAF8F2", "red": "#C43D4B",
    "red_soft": "#FFF0F1", "line": "#DDE3EC", "option": "#F8FAFD",
    "blue_soft": "#EDF2FF", "amber": "#B76E00", "amber_soft": "#FFF7E8",
}


def chapter_of(entry):
    return CATEGORY_TO_CHAPTER.get(entry[1], "其他")


def short_chapter(chapter):
    return chapter.split("  ", 1)[0]


def complete_study_items(chapter=None):
    """统一概念卡与应用题，使学习、浏览、测试使用同一套可见内容。"""
    items = []
    for entry in KNOWLEDGE:
        item_chapter = chapter_of(entry)
        if chapter and item_chapter != chapter:
            continue
        items.append({
            "kind": "knowledge", "key": f"knowledge::{entry[0]}",
            "chapter": item_chapter, "title": entry[0],
            "description": entry[2], "tip": entry[3], "source": entry,
        })
    for question in APPLIED_QUESTIONS:
        if chapter and question["chapter"] != chapter:
            continue
        correct_text = question["options"][question["correct_index"]]
        items.append({
            "kind": "question", "key": f"applied::{question['id']}",
            "chapter": question["chapter"], "title": question["prompt"],
            "description": f"正确答案：{correct_text}",
            "tip": question["explanation"], "source": question,
        })
    return items


class StudyQuiz(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TorchGo·火炬学")
        self.geometry("1020x790")
        self.minsize(900, 700)
        self.configure(bg=COLORS["bg"])

        self.progress = self.load_progress()
        self.study_progress = self.load_study_progress()
        self.session = []
        self.position = 0
        self.session_title = ""
        self.option_buttons = []
        self.chapter_choice = tk.StringVar(value=CHAPTERS[0])
        self.chapter_count = tk.StringVar(value="20题")
        self.random_count = tk.StringVar(value="20题")
        self.chapter_difficulty = tk.StringVar(value="混合难度")
        self.random_difficulty = tk.StringVar(value="混合难度")
        self.study_chapter_choice = tk.StringVar(value=CHAPTERS[0])
        self.study_entries = []
        self.study_position = 0
        self.study_answer_visible = False
        self.timed_session = False
        self.remaining_seconds = 0
        self.timer_job = None

        self._setup_style()
        self.container = tk.Frame(self, bg=COLORS["bg"])
        self.container.pack(fill="both", expand=True)
        self.show_home()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        for number in range(1, 5):
            self.bind(str(number), lambda _event, index=number - 1: self.select_option(index))
        self.bind("<Left>", lambda _event: self.previous_question())
        self.bind("<Right>", lambda _event: self.next_or_submit())

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", padding=8, font=("Microsoft YaHei UI", 10))

    def clear_screen(self):
        for child in self.container.winfo_children():
            child.destroy()
        self.option_buttons = []

    def load_progress(self):
        if not PROGRESS_FILE.exists():
            return {}
        try:
            with PROGRESS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save_progress(self):
        try:
            with PROGRESS_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.progress, file, ensure_ascii=False, indent=2)
        except OSError as exc:
            messagebox.showwarning("保存失败", f"暂时无法保存答题记录：\n{exc}")

    def load_study_progress(self):
        if not STUDY_PROGRESS_FILE.exists():
            return {}
        try:
            with STUDY_PROGRESS_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                return {}
            # 兼容旧版以术语直接作为键的学习记录。
            known_terms = {entry[0] for entry in KNOWLEDGE}
            migrated = {}
            for key, value in data.items():
                new_key = f"knowledge::{key}" if key in known_terms and "::" not in key else key
                migrated[new_key] = value
            return migrated
        except (OSError, json.JSONDecodeError):
            return {}

    def save_study_progress(self):
        try:
            with STUDY_PROGRESS_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.study_progress, file, ensure_ascii=False, indent=2)
        except OSError as exc:
            messagebox.showwarning("保存失败", f"暂时无法保存学习记录：\n{exc}")

    @staticmethod
    def question_key(entry, direction):
        return f"{entry[0]}::{direction}"

    def key_for_question(self, question):
        if question.get("applied_id"):
            return f"applied::{question['applied_id']}"
        return self.question_key(question["entry"], question["direction"])

    @staticmethod
    def chapter_for_question(question):
        return question.get("chapter") or chapter_of(question["entry"])

    @staticmethod
    def prompt_for_question(question):
        if question.get("prompt"):
            return question["prompt"]
        entry = question["entry"]
        if question["direction"] == "term_to_desc":
            return f"以下哪一项最准确地描述了 “{entry[0]}”？"
        return f"“{entry[2]}” 指的是哪个名词？"

    @staticmethod
    def explanation_for_question(question):
        if question.get("explanation"):
            return question["explanation"]
        entry = question["entry"]
        return f"{entry[0]}——{entry[2]}。{entry[3]}"

    def make_button(self, parent, text, command, color=None, width=None):
        color = color or COLORS["primary"]
        return tk.Button(
            parent, text=text, command=command, width=width,
            font=("Microsoft YaHei UI", 10, "bold"), fg="white", bg=color,
            activeforeground="white", activebackground=color, relief="flat",
            padx=17, pady=9, cursor="hand2"
        )

    # ------------------------------ 首页 ------------------------------
    def show_home(self):
        self.clear_screen()
        page = tk.Frame(self.container, bg=COLORS["bg"])
        page.pack(fill="both", expand=True, padx=38, pady=25)

        header = tk.Frame(page, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 13))
        tk.Label(header, text="TorchGo·火炬学", font=("Microsoft YaHei UI", 24, "bold"), fg=COLORS["ink"], bg=COLORS["bg"]).pack(side="left")
        tk.Label(header, text="知识学习 · 章节练习 · 随机测试 · 模拟考试", font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left", padx=18, pady=(12, 0))

        attempts = sum(int(record.get("attempts", 0)) for record in self.progress.values())
        correct = sum(int(record.get("correct", 0)) for record in self.progress.values())
        accuracy = round(correct / attempts * 100) if attempts else 0
        weak = sum(1 for record in self.progress.values() if int(record.get("wrong", 0)) > int(record.get("correct", 0)))
        learnable_total = len(KNOWLEDGE) + len(APPLIED_QUESTIONS)
        studied = sum(1 for record in self.study_progress.values() if record.get("status") == "mastered")
        today_text = date.today().isoformat()
        due_count = sum(1 for record in self.study_progress.values() if record.get("due_date", "9999-12-31") <= today_text)
        summary = tk.Frame(page, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        summary.pack(fill="x", pady=(0, 14))
        tk.Label(summary, text=f"完整题库 {learnable_total} 项（{len(KNOWLEDGE)} 卡片 + {len(APPLIED_QUESTIONS)} 应用题）", font=("Microsoft YaHei UI", 11, "bold"), fg=COLORS["primary"], bg=COLORS["card"]).pack(side="left", padx=18, pady=13)
        tk.Button(summary, text="成绩历史", command=self.show_history, font=("Microsoft YaHei UI", 9), fg=COLORS["primary"], bg=COLORS["card"], activebackground=COLORS["card"], relief="flat", cursor="hand2").pack(side="right", padx=(3, 15))
        tk.Label(summary, text=f"已掌握 {studied}/{learnable_total}  ·  今日复习 {due_count}  ·  答题正确率 {accuracy}%  ·  待强化 {weak}", font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["card"]).pack(side="right", padx=3)

        modes = tk.Frame(page, bg=COLORS["bg"])
        modes.pack(fill="x")
        modes.grid_columnconfigure(0, weight=1, uniform="mode")
        modes.grid_columnconfigure(1, weight=1, uniform="mode")
        modes.grid_columnconfigure(2, weight=1, uniform="mode")

        chapter_card = self.make_card(modes, "章节测试", "选择一章集中检查，交卷后查看本章成绩。", 0)
        ttk.Combobox(chapter_card, textvariable=self.chapter_choice, state="readonly", values=CHAPTERS, width=31).pack(fill="x", pady=(13, 7))
        ttk.Combobox(chapter_card, textvariable=self.chapter_count, state="readonly", values=["10题", "20题", "全部知识点"], width=16).pack(fill="x", pady=(0, 7))
        ttk.Combobox(chapter_card, textvariable=self.chapter_difficulty, state="readonly", values=["混合难度", "基础", "理解", "应用"], width=16).pack(fill="x", pady=(0, 11))
        self.make_button(chapter_card, "开始章节测试", self.start_chapter_test).pack(fill="x")

        random_card = self.make_card(modes, "整体随机测试", "从十章题库随机抽题，快速检查整体掌握度。", 1)
        ttk.Combobox(random_card, textvariable=self.random_count, state="readonly", values=["10题", "20题", "30题"], width=16).pack(fill="x", pady=(15, 7))
        ttk.Combobox(random_card, textvariable=self.random_difficulty, state="readonly", values=["混合难度", "基础", "理解", "应用"], width=16).pack(fill="x", pady=(0, 11))
        self.make_button(random_card, "开始随机测试", self.start_random_test).pack(fill="x")

        exam_card = self.make_card(modes, "50 题模拟考试", "每章均衡抽取 5 题，统一交卷并按章节评分。", 2)
        tk.Label(exam_card, text="建议用时：35 分钟\n满分：100 分", justify="left", font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["card"]).pack(anchor="w", pady=(22, 16))
        self.make_button(exam_card, "开始 50 题考试", self.start_exam, COLORS["red"]).pack(fill="x")
        if UNFINISHED_EXAM_FILE.exists():
            tk.Button(exam_card, text="恢复未完成的考试", command=self.resume_exam, font=("Microsoft YaHei UI", 9), fg=COLORS["primary"], bg=COLORS["card"], activebackground=COLORS["card"], relief="flat", cursor="hand2").pack(anchor="w", pady=(4, 0))

        bottom = tk.Frame(page, bg=COLORS["bg"])
        bottom.pack(fill="both", expand=True, pady=(15, 0))
        left = tk.Frame(bottom, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        tk.Label(left, text="十章知识框架", font=("Microsoft YaHei UI", 12, "bold"), fg=COLORS["ink"], bg=COLORS["card"]).pack(anchor="w", padx=17, pady=(13, 7))
        grid = tk.Frame(left, bg=COLORS["card"])
        grid.pack(fill="both", expand=True, padx=17, pady=(0, 12))
        for index, chapter in enumerate(CHAPTERS):
            count = sum(1 for entry in KNOWLEDGE if chapter_of(entry) == chapter)
            applied_count = sum(1 for item in APPLIED_QUESTIONS if item["chapter"] == chapter)
            label = f"{chapter}  ({count}卡 + {applied_count}题)"
            tk.Label(grid, text=label, anchor="w", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["card"]).grid(row=index % 5, column=index // 5, sticky="w", padx=(0, 22), pady=4)

        right = tk.Frame(bottom, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1, width=300)
        right.pack(side="left", fill="y", padx=(7, 0))
        right.pack_propagate(False)
        tk.Label(right, text="学习模式", font=("Microsoft YaHei UI", 12, "bold"), fg=COLORS["ink"], bg=COLORS["card"]).pack(anchor="w", padx=17, pady=(12, 4))
        ttk.Combobox(right, textvariable=self.study_chapter_choice, state="readonly", values=["全部章节"] + CHAPTERS, width=27).pack(fill="x", padx=17, pady=(0, 6))
        self.make_button(right, "开始完整题库学习", self.start_learning).pack(fill="x", padx=17)
        tk.Button(right, text="浏览所选章节完整题库", command=self.show_question_bank, font=("Microsoft YaHei UI", 9, "bold"), fg=COLORS["primary"], bg=COLORS["card"], activebackground=COLORS["card"], relief="flat", cursor="hand2").pack(anchor="w", padx=13, pady=(3, 0))
        tk.Button(right, text=f"学习今日到期内容（{due_count}）", command=self.start_due_learning, font=("Microsoft YaHei UI", 9), fg=COLORS["primary"], bg=COLORS["card"], activebackground=COLORS["card"], relief="flat", cursor="hand2").pack(anchor="w", padx=13, pady=2)
        tk.Frame(right, bg=COLORS["line"], height=1).pack(fill="x", padx=17, pady=5)
        weak_btn = self.make_button(right, "开始薄弱项复习", self.start_weak_review, COLORS["amber"])
        weak_btn.pack(fill="x", padx=17)
        tk.Button(right, text="清空全部记录", command=self.reset_progress, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["card"], activebackground=COLORS["card"], relief="flat", cursor="hand2").pack(anchor="w", padx=13, pady=4)

    def make_card(self, parent, title, description, column):
        card = tk.Frame(parent, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 7, 0 if column == 2 else 7))
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=17, pady=15)
        tk.Label(inner, text=title, font=("Microsoft YaHei UI", 14, "bold"), fg=COLORS["ink"], bg=COLORS["card"]).pack(anchor="w")
        tk.Label(inner, text=description, wraplength=245, justify="left", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["card"]).pack(anchor="w", pady=(5, 0))
        return inner

    def show_question_bank(self):
        """浏览每章全部概念卡和全部可能被测试抽取的应用题。"""
        window = tk.Toplevel(self)
        window.title("完整章节题库")
        window.geometry("960x740")
        window.minsize(780, 620)
        window.configure(bg=COLORS["bg"])
        window.transient(self)

        selected = self.study_chapter_choice.get()
        chapter_var = tk.StringVar(value=selected if selected in CHAPTERS else CHAPTERS[0])
        type_var = tk.StringVar(value="全部内容")
        search_var = tk.StringVar()

        header = tk.Frame(window, bg=COLORS["bg"])
        header.pack(fill="x", padx=25, pady=(20, 12))
        tk.Label(header, text="完整章节题库", font=("Microsoft YaHei UI", 21, "bold"), fg=COLORS["ink"], bg=COLORS["bg"]).pack(side="left")
        count_label = tk.Label(header, font=("Microsoft YaHei UI", 10, "bold"), fg=COLORS["primary"], bg=COLORS["bg"])
        count_label.pack(side="right", pady=(8, 0))

        controls = tk.Frame(window, bg=COLORS["bg"])
        controls.pack(fill="x", padx=25, pady=(0, 12))
        chapter_box = ttk.Combobox(controls, textvariable=chapter_var, state="readonly", values=CHAPTERS, width=31)
        chapter_box.pack(side="left", padx=(0, 8))
        type_box = ttk.Combobox(controls, textvariable=type_var, state="readonly", values=["全部内容", "知识卡片", "应用题"], width=12)
        type_box.pack(side="left", padx=(0, 8))
        search_entry = tk.Entry(controls, textvariable=search_var, font=("Microsoft YaHei UI", 10), relief="solid", borderwidth=1)
        search_entry.pack(side="left", fill="x", expand=True, ipady=7)
        tk.Label(controls, text="  可搜索名词、题干、答案或解析", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="right")

        outer = tk.Frame(window, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        outer.pack(fill="both", expand=True, padx=25, pady=(0, 22))
        canvas = tk.Canvas(outer, bg=COLORS["card"], highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=COLORS["card"])
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(content_id, width=event.width))
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-event.delta / 120), "units")))
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))

        def render_bank(*_args):
            for child in content.winfo_children():
                child.destroy()
            chapter = chapter_var.get()
            mode = type_var.get()
            query = search_var.get().strip().lower()
            rows = complete_study_items(chapter)
            if mode == "知识卡片":
                rows = [row for row in rows if row["kind"] == "knowledge"]
            elif mode == "应用题":
                rows = [row for row in rows if row["kind"] == "question"]
            if query:
                rows = [row for row in rows if query in " ".join((row["title"], row["description"], row["tip"])).lower()]

            all_rows = complete_study_items(chapter)
            knowledge_count = sum(row["kind"] == "knowledge" for row in all_rows)
            question_count = sum(row["kind"] == "question" for row in all_rows)
            count_label.configure(text=f"本章 {knowledge_count} 张卡片 + {question_count} 道应用题 · 当前显示 {len(rows)} 项")

            if not rows:
                tk.Label(content, text="没有匹配的内容", font=("Microsoft YaHei UI", 11), fg=COLORS["muted"], bg=COLORS["card"]).pack(pady=40)
                return
            for index, row in enumerate(rows, 1):
                block = tk.Frame(content, bg="#FAFBFD", highlightbackground=COLORS["line"], highlightthickness=1)
                block.pack(fill="x", padx=14, pady=(11 if index == 1 else 4, 4))
                kind_text = "知识卡片" if row["kind"] == "knowledge" else "应用题"
                tk.Label(block, text=f"{index}. [{kind_text}] {row['title']}", wraplength=850, justify="left", anchor="w", font=("Microsoft YaHei UI", 11, "bold"), fg=COLORS["ink"], bg="#FAFBFD").pack(fill="x", padx=14, pady=(11, 5))
                if row["kind"] == "question":
                    question = row["source"]
                    options_text = "    ".join(f"{'ABCD'[i]}. {option}" for i, option in enumerate(question["options"]))
                    tk.Label(block, text=options_text, wraplength=850, justify="left", anchor="w", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg="#FAFBFD").pack(fill="x", padx=14, pady=(0, 5))
                tk.Label(block, text=row["description"], wraplength=850, justify="left", anchor="w", font=("Microsoft YaHei UI", 10, "bold"), fg=COLORS["primary"], bg="#FAFBFD").pack(fill="x", padx=14, pady=(0, 4))
                tk.Label(block, text=f"解析：{row['tip']}", wraplength=850, justify="left", anchor="w", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg="#FAFBFD").pack(fill="x", padx=14, pady=(0, 11))
            canvas.yview_moveto(0)

        chapter_box.bind("<<ComboboxSelected>>", render_bank)
        type_box.bind("<<ComboboxSelected>>", render_bank)
        search_var.trace_add("write", render_bank)
        render_bank()

    # ------------------------------ 学习模式 ------------------------------
    def start_learning(self):
        chapter = self.study_chapter_choice.get()
        entries = complete_study_items(None if chapter == "全部章节" else chapter)
        title = chapter

        # 同一优先级内随机排序；已到期最先，新知识其次，未到期最后。
        random.shuffle(entries)
        today_text = date.today().isoformat()
        def study_priority(entry):
            record = self.study_progress.get(entry["key"])
            if record and record.get("due_date", "9999-12-31") <= today_text:
                return 0
            if not record:
                return 1
            return 2
        entries.sort(key=study_priority)
        self.study_entries = entries
        self.study_position = 0
        self.study_title = title
        self.show_learning()

    def start_due_learning(self):
        today_text = date.today().isoformat()
        chapter = self.study_chapter_choice.get()
        entries = [
            entry for entry in complete_study_items(None if chapter == "全部章节" else chapter)
            if self.study_progress.get(entry["key"], {}).get("due_date", "9999-12-31") <= today_text
        ]
        if not entries:
            messagebox.showinfo("今日任务完成", "当前选择范围内没有到期需要复习的知识点。")
            return
        random.shuffle(entries)
        self.study_entries = entries
        self.study_position = 0
        self.study_title = "今日到期复习"
        self.show_learning()

    def show_learning(self):
        self.clear_screen()
        page = tk.Frame(self.container, bg=COLORS["bg"])
        page.pack(fill="both", expand=True, padx=42, pady=27)

        top = tk.Frame(page, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 12))
        tk.Button(top, text="返回首页", command=self.show_home, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"], activebackground=COLORS["bg"], relief="flat", cursor="hand2").pack(side="left")
        tk.Label(top, text="完整题库学习", font=("Microsoft YaHei UI", 18, "bold"), fg=COLORS["ink"], bg=COLORS["bg"]).pack(side="left", padx=18)
        tk.Label(top, text=self.study_title, font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left", pady=(5, 0))
        self.study_counter = tk.Label(top, font=("Microsoft YaHei UI", 10, "bold"), fg=COLORS["muted"], bg=COLORS["bg"])
        self.study_counter.pack(side="right")

        bar_bg = tk.Frame(page, height=7, bg=COLORS["line"])
        bar_bg.pack(fill="x", pady=(0, 15))
        bar_bg.pack_propagate(False)
        self.study_progress_fill = tk.Frame(bar_bg, bg=COLORS["primary"])
        self.study_progress_fill.place(relx=0, rely=0, relheight=1, relwidth=0)

        card = tk.Frame(page, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=42, pady=31)

        self.study_badge = tk.Label(inner, font=("Microsoft YaHei UI", 9, "bold"), fg=COLORS["primary"], bg=COLORS["blue_soft"], padx=10, pady=4)
        self.study_badge.pack(anchor="w")
        self.study_prompt_hint = tk.Label(inner, text="先尝试在脑中解释：", font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["card"])
        self.study_prompt_hint.pack(anchor="w", pady=(24, 5))
        self.study_term = tk.Label(inner, wraplength=820, justify="left", font=("Microsoft YaHei UI", 30, "bold"), fg=COLORS["ink"], bg=COLORS["card"])
        self.study_term.pack(anchor="w", pady=(0, 24))

        self.reveal_study_btn = self.make_button(inner, "查看解释", self.reveal_study_answer)
        self.reveal_study_btn.pack(anchor="w")

        self.study_answer_box = tk.Frame(inner, bg=COLORS["blue_soft"], highlightbackground="#C9D5FA", highlightthickness=1)
        tk.Label(self.study_answer_box, text="核心解释", font=("Microsoft YaHei UI", 10, "bold"), fg=COLORS["primary"], bg=COLORS["blue_soft"]).pack(anchor="w", padx=18, pady=(15, 5))
        self.study_description = tk.Label(self.study_answer_box, wraplength=790, justify="left", font=("Microsoft YaHei UI", 13, "bold"), fg=COLORS["ink"], bg=COLORS["blue_soft"])
        self.study_description.pack(anchor="w", fill="x", padx=18)
        self.study_tip = tk.Label(self.study_answer_box, wraplength=790, justify="left", font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["blue_soft"])
        self.study_tip.pack(anchor="w", fill="x", padx=18, pady=(9, 16))

        self.study_grade_row = tk.Frame(inner, bg=COLORS["card"])
        tk.Label(self.study_grade_row, text="看完后标记掌握程度：", font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["card"]).pack(side="left", padx=(0, 13))
        self.make_button(self.study_grade_row, "已掌握", lambda: self.grade_study("mastered"), COLORS["green"]).pack(side="left", padx=4)
        self.make_button(self.study_grade_row, "有点模糊", lambda: self.grade_study("fuzzy"), COLORS["amber"]).pack(side="left", padx=4)
        self.make_button(self.study_grade_row, "完全不会", lambda: self.grade_study("unknown"), COLORS["red"]).pack(side="left", padx=4)

        bottom = tk.Frame(page, bg=COLORS["bg"])
        bottom.pack(fill="x", pady=(12, 0))
        tk.Label(bottom, text="系统会按 1、3、7、14、30、60 天间隔安排复习", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left")
        tk.Button(bottom, text="暂时跳过 →", command=self.skip_study, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"], activebackground=COLORS["bg"], relief="flat", cursor="hand2").pack(side="right")

        self.render_study_card()

    def render_study_card(self):
        if not self.study_entries:
            self.show_home()
            return
        entry = self.study_entries[self.study_position]
        self.study_answer_visible = False
        self.study_counter.configure(text=f"{self.study_position + 1} / {len(self.study_entries)}")
        self.study_progress_fill.place_configure(relwidth=(self.study_position + 1) / len(self.study_entries))
        type_text = "知识卡片" if entry["kind"] == "knowledge" else "应用题"
        self.study_badge.configure(text=f"{short_chapter(entry['chapter'])} · {type_text}")
        self.study_prompt_hint.configure(text="先尝试在脑中解释这个名词：" if entry["kind"] == "knowledge" else "先独立完成这道题：")
        self.study_term.configure(text=entry["title"], font=("Microsoft YaHei UI", 30 if entry["kind"] == "knowledge" else 18, "bold"))
        self.study_description.configure(text=entry["description"])
        self.study_tip.configure(text=f"补充理解：{entry['tip']}")
        self.study_answer_box.pack_forget()
        self.study_grade_row.pack_forget()
        self.reveal_study_btn.pack(anchor="w")

    def reveal_study_answer(self):
        if self.study_answer_visible:
            return
        self.study_answer_visible = True
        self.reveal_study_btn.pack_forget()
        self.study_answer_box.pack(fill="x", pady=(0, 16))
        self.study_grade_row.pack(fill="x", pady=(2, 0))

    def grade_study(self, status):
        if not self.study_answer_visible or not self.study_entries:
            return
        entry = self.study_entries[self.study_position]
        old = self.study_progress.get(entry["key"], {})
        old_streak = int(old.get("streak", 0))
        if status == "mastered":
            streak = old_streak + 1
            intervals = [1, 3, 7, 14, 30, 60]
            interval_days = intervals[min(streak - 1, len(intervals) - 1)]
        elif status == "fuzzy":
            streak = max(0, old_streak - 1)
            interval_days = 1
        else:
            streak = 0
            interval_days = 0
        self.study_progress[entry["key"]] = {
            "status": status,
            "reviews": int(old.get("reviews", 0)) + 1,
            "streak": streak,
            "due_date": (date.today() + timedelta(days=interval_days)).isoformat(),
            "chapter": entry["chapter"],
            "last_reviewed": datetime.now().isoformat(timespec="seconds"),
        }
        self.save_study_progress()
        self.advance_study()

    def skip_study(self):
        if self.study_entries:
            self.advance_study()

    def advance_study(self):
        if self.study_position >= len(self.study_entries) - 1:
            mastered = sum(1 for entry in self.study_entries if self.study_progress.get(entry["key"], {}).get("status") == "mastered")
            messagebox.showinfo("本轮学习完成", f"本轮已浏览 {len(self.study_entries)} 项题库内容，其中标记掌握 {mastered} 项。")
            self.show_home()
            return
        self.study_position += 1
        self.render_study_card()

    # ------------------------------ 组卷 ------------------------------
    def start_chapter_test(self):
        chapter = self.chapter_choice.get()
        entries = [entry for entry in KNOWLEDGE if chapter_of(entry) == chapter]
        value = self.chapter_count.get()
        applied = [item for item in APPLIED_QUESTIONS if item["chapter"] == chapter]
        if value == "全部知识点":
            variants = [(entry, random.choice(("term_to_desc", "desc_to_term"))) for entry in entries]
            self.build_session_from_variants(variants, f"{chapter} · 章节测试", applied)
            return
        count = int(value.replace("题", ""))
        self.start_mixed_session(entries, applied, count, f"{chapter} · 章节测试", self.chapter_difficulty.get())

    def start_random_test(self):
        count = int(self.random_count.get().replace("题", ""))
        self.start_mixed_session(KNOWLEDGE, APPLIED_QUESTIONS, count, "全书整体随机测试", self.random_difficulty.get())

    def start_exam(self):
        variants = []
        applied_selected = []
        for chapter in CHAPTERS:
            entries = [entry for entry in KNOWLEDGE if chapter_of(entry) == chapter]
            chapter_applied = [item for item in APPLIED_QUESTIONS if item["chapter"] == chapter]
            chosen_entries = random.sample(entries, min(3, len(entries)))
            variants.extend((entry, random.choice(("term_to_desc", "desc_to_term"))) for entry in chosen_entries)
            applied_selected.extend(random.sample(chapter_applied, min(2, len(chapter_applied))))
        self.build_session_from_variants(variants, "50 题模拟考试", applied_selected, timed=True)

    def start_weak_review(self):
        weak_variants = []
        weak_applied = []
        entry_by_term = {entry[0]: entry for entry in KNOWLEDGE}
        applied_by_id = {item["id"]: item for item in APPLIED_QUESTIONS}
        for key, record in self.progress.items():
            if int(record.get("wrong", 0)) <= int(record.get("correct", 0)):
                continue
            if key.startswith("applied::"):
                qid = key.split("::", 1)[1]
                if qid in applied_by_id:
                    weak_applied.append(applied_by_id[qid])
                continue
            if "::" not in key:
                continue
            term, direction = key.rsplit("::", 1)
            if term in entry_by_term and direction in ("term_to_desc", "desc_to_term"):
                weak_variants.append((entry_by_term[term], direction))
        if not weak_variants and not weak_applied:
            messagebox.showinfo("暂无错题", "目前没有需要重点复习的错题。先完成一次章节或随机测试吧。")
            return
        random.shuffle(weak_variants)
        random.shuffle(weak_applied)
        remaining = max(0, 30 - len(weak_applied))
        self.build_session_from_variants(weak_variants[:remaining], "薄弱项专项复习", weak_applied[:30])

    def start_mixed_session(self, entries, applied_pool, count, title, difficulty="混合难度"):
        if not entries:
            messagebox.showinfo("没有题目", "这一章节暂时没有可用题目。")
            return
        if difficulty != "混合难度":
            filtered = [item for item in applied_pool if item["difficulty"] == difficulty]
            applied_pool = filtered or applied_pool
        applied_target = min(len(applied_pool), max(1, count // (2 if difficulty != "混合难度" else 3)))
        chosen_applied = random.sample(applied_pool, applied_target) if applied_target else []
        knowledge_count = min(len(entries), count - len(chosen_applied))
        chosen = random.sample(entries, knowledge_count)
        variants = [(entry, random.choice(("term_to_desc", "desc_to_term"))) for entry in chosen]
        self.build_session_from_variants(variants, title, chosen_applied)

    def build_session_from_variants(self, variants, title, applied=None, timed=False):
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.session = []
        for entry, direction in variants:
            options, correct_index = self.build_options(entry, direction)
            self.session.append({
                "entry": entry, "direction": direction, "options": options,
                "correct_index": correct_index, "selected": None, "marked": False,
            })
        for item in applied or []:
            options = list(item["options"])
            correct_value = options[item["correct_index"]]
            random.shuffle(options)
            self.session.append({
                "entry": None, "direction": "applied", "applied_id": item["id"],
                "chapter": item["chapter"], "question_type": item["type"],
                "difficulty": item["difficulty"], "prompt": item["prompt"],
                "options": options, "correct_index": options.index(correct_value),
                "selected": None, "marked": False, "explanation": item["explanation"],
            })
        random.shuffle(self.session)
        self.position = 0
        self.session_title = title
        self.timed_session = timed
        self.remaining_seconds = 35 * 60 if timed else 0
        self.show_quiz()
        if timed:
            self.save_unfinished_exam()
            self.update_timer()

    def build_options(self, entry, direction):
        same_chapter = [candidate for candidate in KNOWLEDGE if chapter_of(candidate) == chapter_of(entry) and candidate[0] != entry[0]]
        other = [candidate for candidate in KNOWLEDGE if candidate[0] != entry[0] and candidate not in same_chapter]
        random.shuffle(same_chapter)
        random.shuffle(other)
        pool = same_chapter + other
        distractors = pool[:3]
        if direction == "term_to_desc":
            values = [entry[2]] + [candidate[2] for candidate in distractors]
        else:
            values = [entry[0]] + [candidate[0] for candidate in distractors]
        correct_value = values[0]
        random.shuffle(values)
        return values, values.index(correct_value)

    # ------------------------------ 答题页 ------------------------------
    def show_quiz(self):
        self.clear_screen()
        page = tk.Frame(self.container, bg=COLORS["bg"])
        page.pack(fill="both", expand=True, padx=38, pady=24)

        top = tk.Frame(page, bg=COLORS["bg"])
        top.pack(fill="x", pady=(0, 11))
        tk.Button(top, text="退出测试", command=self.exit_session, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"], activebackground=COLORS["bg"], relief="flat", cursor="hand2").pack(side="left")
        self.quiz_title = tk.Label(top, text=self.session_title, font=("Microsoft YaHei UI", 15, "bold"), fg=COLORS["ink"], bg=COLORS["bg"])
        self.quiz_title.pack(side="left", padx=18)
        self.timer_label = tk.Label(top, font=("Microsoft YaHei UI", 11, "bold"), fg=COLORS["red"], bg=COLORS["bg"])
        self.timer_label.pack(side="right", padx=(12, 0))
        tk.Button(top, text="答题卡", command=self.show_answer_sheet, font=("Microsoft YaHei UI", 9, "bold"), fg=COLORS["primary"], bg=COLORS["bg"], activebackground=COLORS["bg"], relief="flat", cursor="hand2").pack(side="right", padx=10)
        tk.Label(top, text="交卷后公布答案", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="right")

        progress_bg = tk.Frame(page, height=7, bg=COLORS["line"])
        progress_bg.pack(fill="x", pady=(0, 12))
        progress_bg.pack_propagate(False)
        self.progress_fill = tk.Frame(progress_bg, bg=COLORS["primary"])
        self.progress_fill.place(relx=0, rely=0, relheight=1, relwidth=0)

        card = tk.Frame(page, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=34, pady=25)

        meta = tk.Frame(inner, bg=COLORS["card"])
        meta.pack(fill="x")
        self.chapter_badge = tk.Label(meta, font=("Microsoft YaHei UI", 9, "bold"), fg=COLORS["primary"], bg=COLORS["blue_soft"], padx=10, pady=4)
        self.chapter_badge.pack(side="left")
        self.counter_label = tk.Label(meta, font=("Microsoft YaHei UI", 10, "bold"), fg=COLORS["muted"], bg=COLORS["card"])
        self.counter_label.pack(side="right")

        self.prompt_label = tk.Label(inner, wraplength=850, justify="left", anchor="w", font=("Microsoft YaHei UI", 18, "bold"), fg=COLORS["ink"], bg=COLORS["card"])
        self.prompt_label.pack(fill="x", pady=(19, 18))

        options_frame = tk.Frame(inner, bg=COLORS["card"])
        options_frame.pack(fill="x")
        for index in range(4):
            button = tk.Button(
                options_frame, command=lambda i=index: self.select_option(i),
                font=("Microsoft YaHei UI", 10), justify="left", anchor="w",
                wraplength=790, fg=COLORS["ink"], bg=COLORS["option"],
                activeforeground=COLORS["ink"], activebackground=COLORS["blue_soft"],
                relief="solid", borderwidth=1, padx=16, pady=12, cursor="hand2"
            )
            button.pack(fill="x", pady=6)
            self.option_buttons.append(button)

        nav = tk.Frame(page, bg=COLORS["bg"])
        nav.pack(fill="x", pady=(12, 0))
        self.previous_btn = self.make_button(nav, "← 上一题", self.previous_question, "#7C879B")
        self.previous_btn.pack(side="left")
        self.answered_label = tk.Label(nav, font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"])
        self.answered_label.pack(side="left", padx=18)
        self.mark_btn = tk.Button(nav, text="标记复查", command=self.toggle_mark, font=("Microsoft YaHei UI", 9, "bold"), fg=COLORS["amber"], bg=COLORS["bg"], activebackground=COLORS["bg"], relief="flat", cursor="hand2")
        self.mark_btn.pack(side="left")
        self.next_btn = self.make_button(nav, "下一题 →", self.next_or_submit)
        self.next_btn.pack(side="right")

        self.render_question()

    def render_question(self):
        if not self.session:
            return
        question = self.session[self.position]
        badge = short_chapter(self.chapter_for_question(question))
        if question.get("question_type"):
            badge += f"  ·  {question['question_type']}  ·  {question.get('difficulty', '')}"
        self.chapter_badge.configure(text=badge)
        self.counter_label.configure(text=f"第 {self.position + 1} / {len(self.session)} 题")
        self.prompt_label.configure(text=self.prompt_for_question(question))

        letters = "ABCD"
        for index, button in enumerate(self.option_buttons):
            selected = question["selected"] == index
            button.configure(
                text=f"{letters[index]}.  {question['options'][index]}",
                fg=COLORS["primary"] if selected else COLORS["ink"],
                bg=COLORS["blue_soft"] if selected else COLORS["option"],
                relief="solid"
            )
        answered = sum(item["selected"] is not None for item in self.session)
        self.answered_label.configure(text=f"已作答 {answered} 题")
        self.previous_btn.configure(state="normal" if self.position > 0 else "disabled")
        self.next_btn.configure(text="交卷" if self.position == len(self.session) - 1 else "下一题 →")
        self.mark_btn.configure(text="取消标记" if question.get("marked") else "标记复查")
        self.progress_fill.place_configure(relwidth=(self.position + 1) / len(self.session))
        if self.timed_session:
            self.save_unfinished_exam()

    def select_option(self, index):
        if not self.session or not 0 <= index < 4:
            return
        self.session[self.position]["selected"] = index
        self.render_question()

    def toggle_mark(self):
        if not self.session:
            return
        question = self.session[self.position]
        question["marked"] = not question.get("marked", False)
        self.render_question()

    def show_answer_sheet(self):
        if not self.session:
            return
        window = tk.Toplevel(self)
        window.title("答题卡")
        window.geometry("620x430")
        window.configure(bg=COLORS["bg"])
        window.transient(self)
        tk.Label(window, text="答题卡", font=("Microsoft YaHei UI", 18, "bold"), fg=COLORS["ink"], bg=COLORS["bg"]).pack(anchor="w", padx=24, pady=(20, 5))
        tk.Label(window, text="蓝色：已作答   黄色：标记复查   灰色：未作答", font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w", padx=24)
        grid = tk.Frame(window, bg=COLORS["bg"])
        grid.pack(fill="both", expand=True, padx=24, pady=16)

        def jump(index):
            self.position = index
            self.render_question()
            window.destroy()

        for index, question in enumerate(self.session):
            if question.get("marked"):
                color = COLORS["amber"]
            elif question.get("selected") is not None:
                color = COLORS["primary"]
            else:
                color = "#9AA4B5"
            tk.Button(grid, text=str(index + 1), command=lambda i=index: jump(i), width=4, font=("Microsoft YaHei UI", 9, "bold"), fg="white", bg=color, activeforeground="white", activebackground=color, relief="flat", pady=7, cursor="hand2").grid(row=index // 10, column=index % 10, padx=4, pady=4)

    def save_unfinished_exam(self):
        if not self.timed_session or not self.session:
            return
        payload = {
            "session": self.session, "position": self.position,
            "title": self.session_title, "remaining_seconds": self.remaining_seconds,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        try:
            with UNFINISHED_EXAM_FILE.open("w", encoding="utf-8") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def resume_exam(self):
        try:
            with UNFINISHED_EXAM_FILE.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            session = payload.get("session", [])
            if not session:
                raise ValueError("empty session")
            for question in session:
                question.setdefault("marked", False)
            self.session = session
            self.position = min(int(payload.get("position", 0)), len(session) - 1)
            self.session_title = payload.get("title", "50 题模拟考试")
            self.remaining_seconds = max(1, int(payload.get("remaining_seconds", 35 * 60)))
            self.timed_session = True
            self.show_quiz()
            self.update_timer()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            messagebox.showwarning("无法恢复", "未完成考试记录已损坏或不存在。")

    def update_timer(self):
        if not self.timed_session or not self.session:
            return
        minutes, seconds = divmod(max(0, self.remaining_seconds), 60)
        if hasattr(self, "timer_label") and self.timer_label.winfo_exists():
            self.timer_label.configure(text=f"剩余 {minutes:02d}:{seconds:02d}")
        if self.remaining_seconds <= 0:
            self.timer_job = None
            messagebox.showinfo("考试时间到", "考试时间已结束，系统将自动交卷。")
            self.finish_session()
            return
        self.remaining_seconds -= 1
        if self.remaining_seconds % 10 == 0:
            self.save_unfinished_exam()
        self.timer_job = self.after(1000, self.update_timer)

    def on_close(self):
        if self.timed_session and self.session:
            self.save_unfinished_exam()
        self.destroy()

    def previous_question(self):
        if self.session and self.position > 0:
            self.position -= 1
            self.render_question()

    def next_or_submit(self):
        if not self.session:
            return
        if self.session[self.position]["selected"] is None:
            messagebox.showinfo("尚未作答", "请先选择一个答案。")
            return
        if self.position < len(self.session) - 1:
            self.position += 1
            self.render_question()
        else:
            unanswered = sum(item["selected"] is None for item in self.session)
            if unanswered:
                messagebox.showinfo("还有未答题", f"还有 {unanswered} 道题未作答，请返回完成后再交卷。")
                return
            self.finish_session()

    def exit_session(self):
        message = "退出后可从首页恢复本次考试。" if self.timed_session else "当前答案不会保存。"
        if messagebox.askyesno("退出测试", f"确定退出本次测试吗？{message}"):
            if self.timed_session:
                self.save_unfinished_exam()
            if self.timer_job:
                self.after_cancel(self.timer_job)
                self.timer_job = None
            self.session = []
            self.timed_session = False
            self.show_home()

    # ------------------------------ 成绩页 ------------------------------
    def finish_session(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        now = datetime.now().isoformat(timespec="seconds")
        for question in self.session:
            key = self.key_for_question(question)
            is_correct = question["selected"] == question["correct_index"]
            record = self.progress.get(key, {"attempts": 0, "correct": 0, "wrong": 0})
            record["attempts"] = int(record.get("attempts", 0)) + 1
            record["correct"] = int(record.get("correct", 0)) + int(is_correct)
            record["wrong"] = int(record.get("wrong", 0)) + int(not is_correct)
            record["last_answered"] = now
            self.progress[key] = record
        self.save_progress()
        self.append_history(now)
        if UNFINISHED_EXAM_FILE.exists():
            try:
                UNFINISHED_EXAM_FILE.unlink()
            except OSError:
                pass
        self.timed_session = False
        self.show_results()

    def append_history(self, timestamp):
        total = len(self.session)
        correct = sum(question["selected"] == question["correct_index"] for question in self.session)
        chapter_scores = {}
        for chapter in CHAPTERS:
            items = [question for question in self.session if self.chapter_for_question(question) == chapter]
            if items:
                chapter_scores[short_chapter(chapter)] = {
                    "correct": sum(question["selected"] == question["correct_index"] for question in items),
                    "total": len(items),
                }
        history = []
        if HISTORY_FILE.exists():
            try:
                with HISTORY_FILE.open("r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, list):
                    history = loaded
            except (OSError, json.JSONDecodeError):
                history = []
        history.append({
            "time": timestamp, "title": self.session_title, "score": round(correct / total * 100) if total else 0,
            "correct": correct, "total": total, "chapters": chapter_scores,
        })
        try:
            with HISTORY_FILE.open("w", encoding="utf-8") as file:
                json.dump(history[-100:], file, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def show_results(self):
        self.clear_screen()
        total = len(self.session)
        correct = sum(question["selected"] == question["correct_index"] for question in self.session)
        score = round(correct / total * 100) if total else 0
        if score >= 90:
            verdict, verdict_color = "优秀，基础非常扎实", COLORS["green"]
        elif score >= 80:
            verdict, verdict_color = "良好，再复习少量薄弱点", COLORS["primary"]
        elif score >= 60:
            verdict, verdict_color = "及格，建议按章节强化", COLORS["amber"]
        else:
            verdict, verdict_color = "需要巩固，先从错题开始", COLORS["red"]

        page = tk.Frame(self.container, bg=COLORS["bg"])
        page.pack(fill="both", expand=True, padx=38, pady=24)
        header = tk.Frame(page, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 12))
        tk.Label(header, text="测试结果", font=("Microsoft YaHei UI", 23, "bold"), fg=COLORS["ink"], bg=COLORS["bg"]).pack(side="left")
        tk.Label(header, text=self.session_title, font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["bg"]).pack(side="left", padx=17, pady=(10, 0))

        score_card = tk.Frame(page, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        score_card.pack(fill="x", pady=(0, 12))
        tk.Label(score_card, text=str(score), font=("Microsoft YaHei UI", 38, "bold"), fg=verdict_color, bg=COLORS["card"]).pack(side="left", padx=(24, 4), pady=14)
        tk.Label(score_card, text="分", font=("Microsoft YaHei UI", 15, "bold"), fg=verdict_color, bg=COLORS["card"]).pack(side="left", pady=(28, 0))
        tk.Label(score_card, text=f"{verdict}\n答对 {correct} 题 · 答错 {total - correct} 题 · 共 {total} 题", justify="left", font=("Microsoft YaHei UI", 10), fg=COLORS["muted"], bg=COLORS["card"]).pack(side="left", padx=22)
        self.make_button(score_card, "返回首页", self.show_home).pack(side="right", padx=20)

        body = tk.Frame(page, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)
        chapter_card = tk.Frame(body, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1, width=280)
        chapter_card.pack(side="left", fill="y", padx=(0, 7))
        chapter_card.pack_propagate(False)
        tk.Label(chapter_card, text="章节得分", font=("Microsoft YaHei UI", 12, "bold"), fg=COLORS["ink"], bg=COLORS["card"]).pack(anchor="w", padx=17, pady=(14, 8))
        for chapter in CHAPTERS:
            chapter_questions = [q for q in self.session if self.chapter_for_question(q) == chapter]
            if not chapter_questions:
                continue
            chapter_correct = sum(q["selected"] == q["correct_index"] for q in chapter_questions)
            percentage = round(chapter_correct / len(chapter_questions) * 100)
            row = tk.Frame(chapter_card, bg=COLORS["card"])
            row.pack(fill="x", padx=17, pady=3)
            tk.Label(row, text=short_chapter(chapter), font=("Microsoft YaHei UI", 9), fg=COLORS["muted"], bg=COLORS["card"]).pack(side="left")
            tk.Label(row, text=f"{chapter_correct}/{len(chapter_questions)}  {percentage}%", font=("Microsoft YaHei UI", 9, "bold"), fg=COLORS["green"] if percentage >= 80 else COLORS["red"], bg=COLORS["card"]).pack(side="right")

        review_card = tk.Frame(body, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        review_card.pack(side="left", fill="both", expand=True, padx=(7, 0))
        tk.Label(review_card, text="错题解析", font=("Microsoft YaHei UI", 12, "bold"), fg=COLORS["ink"], bg=COLORS["card"]).pack(anchor="w", padx=17, pady=(14, 8))
        text_frame = tk.Frame(review_card, bg=COLORS["card"])
        text_frame.pack(fill="both", expand=True, padx=13, pady=(0, 13))
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        review = tk.Text(text_frame, wrap="word", font=("Microsoft YaHei UI", 9), fg=COLORS["ink"], bg="#FAFBFD", relief="flat", padx=10, pady=8, yscrollcommand=scrollbar.set)
        review.pack(fill="both", expand=True)
        scrollbar.configure(command=review.yview)
        wrong_questions = [q for q in self.session if q["selected"] != q["correct_index"]]
        if not wrong_questions:
            review.insert("end", "本次测试全部正确，没有错题。\n\n继续保持！")
        else:
            for index, question in enumerate(wrong_questions, 1):
                prompt = self.prompt_for_question(question)
                selected_text = "未作答" if question["selected"] is None else question["options"][question["selected"]]
                correct_text = question["options"][question["correct_index"]]
                review.insert("end", f"{index}. [{short_chapter(self.chapter_for_question(question))}] {prompt}\n")
                review.insert("end", f"你的答案：{selected_text}\n")
                review.insert("end", f"正确答案：{correct_text}\n")
                review.insert("end", f"解析：{self.explanation_for_question(question)}\n\n")
        review.configure(state="disabled")

    def show_history(self):
        history = []
        if HISTORY_FILE.exists():
            try:
                with HISTORY_FILE.open("r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, list):
                    history = loaded
            except (OSError, json.JSONDecodeError):
                history = []
        window = tk.Toplevel(self)
        window.title("成绩历史")
        window.geometry("700x520")
        window.configure(bg=COLORS["bg"])
        tk.Label(window, text="历次测试成绩", font=("Microsoft YaHei UI", 19, "bold"), fg=COLORS["ink"], bg=COLORS["bg"]).pack(anchor="w", padx=24, pady=(20, 10))
        frame = tk.Frame(window, bg=COLORS["card"], highlightbackground=COLORS["line"], highlightthickness=1)
        frame.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        text_widget = tk.Text(frame, wrap="word", font=("Microsoft YaHei UI", 10), fg=COLORS["ink"], bg=COLORS["card"], relief="flat", padx=15, pady=12, yscrollcommand=scrollbar.set)
        text_widget.pack(fill="both", expand=True)
        scrollbar.configure(command=text_widget.yview)
        if not history:
            text_widget.insert("end", "还没有完成过测试。完成章节测试、随机测试或模拟考试后，成绩会保存在这里。")
        else:
            for index, item in enumerate(reversed(history), 1):
                time_text = str(item.get("time", "")).replace("T", " ")
                text_widget.insert("end", f"{index}. {item.get('title', '测试')}\n")
                text_widget.insert("end", f"   {time_text}   {item.get('score', 0)} 分   {item.get('correct', 0)}/{item.get('total', 0)} 题\n")
                chapter_text = "  ".join(f"{name}:{value.get('correct', 0)}/{value.get('total', 0)}" for name, value in item.get("chapters", {}).items())
                if chapter_text:
                    text_widget.insert("end", f"   {chapter_text}\n")
                text_widget.insert("end", "\n")
        text_widget.configure(state="disabled")

    def reset_progress(self):
        if not messagebox.askyesno("清空全部记录", "确定清空学习进度、历史成绩和错题记录吗？此操作无法撤销。"):
            return
        self.progress = {}
        self.study_progress = {}
        self.save_progress()
        self.save_study_progress()
        for path in (HISTORY_FILE, UNFINISHED_EXAM_FILE):
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass
        self.show_home()


if __name__ == "__main__":
    StudyQuiz().mainloop()
