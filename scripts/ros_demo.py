#!/usr/bin/env python3
"""Walk through one scheduler loop on the fictional demo graph, in a temporary copy.

    python3 scripts/ros_demo.py [--lang en|zh-CN]
    python3 scripts/ros_demo.py --init personal_vault   # start your own vault from the demo graph

Steps: session start -> a source card changes -> the judgment that depends on it is
flagged -> the researcher re-checks; the public starter shows the reconfirmation as a
planned change instead of writing it (the public starter only offers a copy fallback) -> session
close. The tracked demo files are never modified.

``--init <folder>`` copies the demo graph into a folder that has no portfolio yet, leaving out what a
walk-through on the fixture leaves behind (its ros records and the sample answer) and the fictional
judgment, and prints the next steps.
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ros  # noqa: E402

DEMO = ROOT / "examples" / "scheduler-demo"
TODAY = "2026-09-20"


class Terminal(io.StringIO):
    """The researcher's terminal: ros asks its y/N question only there."""

    def isatty(self) -> bool:
        return True


# Narration in both languages; the ros output itself follows --lang.
NARRATION = {
    "en": {
        "skip": "On a first read you can skip the counter lines (\"scope / | … keys\", \"Unknowns, kept apart\", "
                "\"Budget: boundaries\"); they are bookkeeping.",
        "1": "1. ros today — first session: the existing judgment has no admission receipt yet",
        "2": "2. ros admit --confirm — the researcher confirms it after the fact at the researcher's own terminal "
             "(the demo types y; it was written without prior authorization, so this is not an admission)",
        "3": "3. A source changes (the benchmark protocol is revised); ros today flags the judgment that depends on it",
        "4": "4. ros state — Q, E, J, B and N of the commitment",
        "5": "5. After re-checking, the researcher asks to reconfirm; the public starter shows the planned change "
             "and writes nothing (copy fallback)",
        "6": "6. ros close — the session ends with the re-check still listed as pending",
        "next": "What next",
        "next.body": [
            "  · Walk through it yourself on the fixture: docs/user-manual.en.md §3.",
            "  · Start your own:",
            "      python3 scripts/ros_demo.py --init personal_vault",
            "    then edit personal_vault/06_active_context/research-portfolio.md and run",
            "      python3 scripts/ros.py --root personal_vault today",
            "  · `ros …` in the output above means `python3 scripts/ros.py --root <folder> …`.",
        ],
        "init.exists": "ros_demo: {portfolio} already exists; --init only starts a folder that has no portfolio yet",
        "init.title": "My Research Commitments",
        "init.done": [
            "Started {folder}/ from the fictional demo graph, without the demo's ros records, sample answer "
            "and judgment. Next:",
            "  1. In {folder}/06_active_context/research-portfolio.md, replace the two fictional commitments "
            "with one of your own (fields: docs/user-manual.en.md §5).",
            "  2. Replace the two fictional cards under {folder}/01_knowledge/ with one card of your own at the "
            "path its source_path names, starting from a template in 09_templates/ such as project-template.md.",
            "  3. Run: python3 scripts/ros.py --root {folder} today",
        ],
    },
    "zh-CN": {
        "skip": "第一次读可以跳过几行计数（「范围 /｜… 个键」「未知分三类」「预算：boundaries」），它们是记账用的。",
        "1": "1. ros today — 第一个会话：已有的判断还没有准入回执",
        "2": "2. ros admit --confirm — 研究者在自己的终端上事后确认（演示代为输入 y；它写入时没有事先授权，所以这不是准入）",
        "3": "3. 来源变化（基准协议改版）；ros today 标出依赖它的判断",
        "4": "4. ros state — 这项承诺的 Q、E、J、B、N",
        "5": "5. 复核后研究者要求重新确认；公开 starter 只展示计划中的改动，不写入（复制回退）",
        "6": "6. ros close — 会话结束，复核仍列为待处理",
        "next": "接下来",
        "next.body": [
            "  · 在这个示例上自己走一遍：docs/user-manual.zh.md 第 3 节。",
            "  · 开始自己的：",
            "      python3 scripts/ros_demo.py --init personal_vault --lang zh-CN",
            "    然后编辑 personal_vault/06_active_context/research-portfolio.md，再运行",
            "      python3 scripts/ros.py --root personal_vault today",
            "  · 上面输出里的 `ros …` 指 `python3 scripts/ros.py --root <文件夹> …`。",
        ],
        "init.exists": "ros_demo：{portfolio} 已经存在；--init 只用于还没有任务总表的文件夹",
        "init.title": "我的研究承诺",
        "init.done": [
            "已从虚构演示图建好 {folder}/，演示的 ros 记录、示例回答和判断没有带过来。接下来：",
            "  1. 在 {folder}/06_active_context/research-portfolio.md 里，把两项虚构承诺换成你自己的一项"
            "（字段见 docs/user-manual.zh.md 第 5 节）。",
            "  2. 把 {folder}/01_knowledge/ 下的两张虚构卡片换成你自己的一张，放在 source_path 指向的位置，"
            "可以从 09_templates/ 里的模板（如 project-template.md）开始。",
            "  3. 运行：python3 scripts/ros.py --root {folder} today",
        ],
    },
}


def run(root: Path, *argv: str, lang: str = "en", answer: str = "") -> str:
    """Run ros once. With ``answer``, the demo types that reply at the terminal prompt for the researcher."""
    buffer, prompt = io.StringIO(), Terminal()
    saved = sys.stdin, sys.stderr
    if answer:
        sys.stdin, sys.stderr = Terminal(answer + "\n"), prompt
    try:
        with redirect_stdout(buffer):
            ros.main(["--root", str(root), "--today", TODAY, "--lang", lang, *argv])
    finally:
        sys.stdin, sys.stderr = saved
    return (prompt.getvalue() + answer + "\n" if answer else "") + buffer.getvalue()


def step(title: str, output: str) -> None:
    print(f"\n━━ {title}\n")
    print(output.rstrip())


def init(folder: str, say: dict, lang: str = "en") -> int:
    """Copy the demo graph into ``folder`` the way the demo's temporary copy is made, minus the sample answer
    and the fictional judgment; files already in the folder are kept."""
    target = Path(folder)
    portfolio = target / "06_active_context" / "research-portfolio.md"
    if portfolio.exists():
        print(say["init.exists"].format(portfolio=portfolio.as_posix()), file=sys.stderr)
        return 2

    def copy_new(source: str, destination: str) -> None:
        if not Path(destination).exists():
            shutil.copy2(source, destination)
    shutil.copytree(DEMO, target, ignore=shutil.ignore_patterns("work_state", "sample-answer.md"),
                    copy_function=copy_new, dirs_exist_ok=True)
    text = portfolio.read_text(encoding="utf-8")
    text = re.sub(r"^- judgments:.*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n> \[!judgment\][^\n]*\n(?:>[^\n]*\n)*", "", text)
    text = text.replace("Demo Commitments (fictional)", say["init.title"])
    config = target / "config" / "ros.json"
    config.write_text(config.read_text(encoding="utf-8").replace('"language": "en"', f'"language": "{lang}"'), encoding="utf-8")
    portfolio.write_text(text, encoding="utf-8")
    shown = target.as_posix().rstrip("/")
    print("\n".join(say["init.done"]).format(folder=shown))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", choices=["en", "zh-CN"], default="en")
    parser.add_argument("--init", metavar="FOLDER", help="start your own vault in FOLDER from the demo graph")
    args = parser.parse_args(argv)
    lang = args.lang
    say = NARRATION[lang]
    if args.init:
        return init(args.init, say, lang)
    with tempfile.TemporaryDirectory(prefix="ros-demo-") as tmp:
        root = Path(tmp) / "scheduler-demo"
        shutil.copytree(DEMO, root, ignore=shutil.ignore_patterns("work_state"))
        step(say["1"], say["skip"] + "\n\n" + run(root, "today", lang=lang))
        step(say["2"], run(root, "admit", "--confirm", "j-occlusion-scope", lang=lang, answer="y"))
        benchmark = root / "01_knowledge" / "papers" / "example-benchmark.md"
        benchmark.write_text(benchmark.read_text(encoding="utf-8").replace(
            "Version 1 of the protocol.", "Version 2 of the protocol: the heavy-occlusion split was relabelled."),
            encoding="utf-8")
        # The same intent on the same day continues session 1; `today --for` would open a second session.
        step(say["3"], run(root, "today", lang=lang))
        step(say["4"], run(root, "state", "occlusion-paper", lang=lang))
        step(say["5"], run(root, "admit", "--reconfirm", "j-occlusion-scope", lang=lang))
        step(say["6"], run(root, "close", lang=lang))
    step(say["next"], "\n".join(say["next.body"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
