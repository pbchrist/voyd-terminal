#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ACT1 = ROOT / "data" / "act1_nodes.json"
ACT2 = ROOT / "data" / "story_graph.json"
OUT = ROOT / "STORY.md"

TITLE_OVERRIDES = {
    "1.0": "The Threshold",
    "2.1": "Press With What Is Missing",
    "2.2": "Press With What You Want",
    "revelation.di": "The Edge of Its Power",
    "revelation.ck": "What the Voyd Cannot Restore",
    "revelation.dm": "What Intention Feeds",
    "revelation.ib": "The Name It Uses as Bait",
    "threshold.di": "Leave With the Rule, or Ask for More",
    "threshold.ck": "Leave With the Distinction, or Test It",
    "threshold.dm": "Leave With the Knowledge, or Bargain",
    "threshold.ib": "Leave With the Hook Exposed, or Bargain",
    "entry_unbound": "Walk Away Free",
    "entry_petition": "Name the Change",
    "entry_declined": "Refuse to Name It",
    "entry_reframe": "Ask for the Present, Not the Past",
    "entry_counterforce": "The World Pushes Back",
    "entry_offer": "The Terms",
    "entry_accepted": "The Debt You Accepted",
    "entry_refused": "Refuse the Bargain",
    "entry_fulfilled": "The Debt Is Paid",
    "entry_breached": "The Debt Is Broken",
    "approach": "At the Threshold Again",
    "inquiry_name": "Ask What It Is",
    "inquiry_place": "Ask Where You Are",
    "confession": "Give It Something Heavy",
    "challenge": "Defy It",
    "silence": "Say Nothing",
    "memory_soryn": "Sory'n",
    "memory_orachys": "Orachys",
    "memory_severing": "The Severing",
    "memory_leoran": "Leoran",
    "memory_sol": "Denidrata",
    "memory_springs": "The Wellsprings",
    "memory_nullstate": "The Null State",
    "gravity": "The Direction of the Fall",
    "mirror": "The Voice in the Glass",
    "choice": "The Portal Forms",
    "ending_hunger": "Reach With Hunger",
    "ending_grief": "Reach With Grief",
    "ending_silence": "Choose Silence",
    "ending_question": "Leave With a Question",
}


def anchor(value: str) -> str:
    return value.lower().replace(".", "").replace("_", "-").replace(" ", "-")


def title_for(node_id: str, node: dict) -> str:
    if node_id in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[node_id]
    label = node.get("reader_title") or node.get("label") or node.get("type") or node_id
    return label.replace("_", " ").title()


def transition_label(target: str, node: dict) -> str:
    explicit = node.get("reader_transition")
    if explicit:
        return explicit
    return TITLE_OVERRIDES.get(target, target.replace("_", " ").title())


def render_act1(nodes: dict) -> list[str]:
    lines = ["## Act I — The Threshold", ""]
    for node_id, node in nodes.items():
        lines += [f'<a id="{anchor(node_id)}"></a>', f"### {title_for(node_id, node)}", ""]
        text = (node.get("text") or "").strip()
        if text:
            lines += [text, ""]
        choices = node.get("choices", [])
        if choices:
            lines += ["**What do you do?**", ""]
            for choice in choices:
                target = choice.get("next", "")
                label = (choice.get("reader_label") or choice.get("label") or "continue").strip()
                if target == "ACT2":
                    lines.append(f"- **{label}** → [enter Act II](#act-ii--the-live-bargain)")
                else:
                    lines.append(f"- [{label}](#{anchor(target)})")
            lines.append("")
    return lines


def render_act2(nodes: dict) -> list[str]:
    lines = ['<a id="act-ii--the-live-bargain"></a>', "## Act II — The Live Bargain", ""]
    order = [
        "entry_unbound", "entry_petition", "entry_declined", "entry_reframe",
        "entry_counterforce", "entry_offer", "entry_accepted", "entry_refused",
        "entry_fulfilled", "entry_breached", "approach", "inquiry_name",
        "inquiry_place", "confession", "challenge", "silence", "memory_soryn",
        "memory_orachys", "memory_severing", "memory_leoran", "memory_sol",
        "memory_springs", "memory_nullstate", "gravity", "mirror", "choice",
        "ending_hunger", "ending_grief", "ending_silence", "ending_question",
    ]
    for node_id in order:
        node = nodes.get(node_id)
        if not node:
            continue
        lines += [f'<a id="{anchor(node_id)}"></a>', f"### {title_for(node_id, node)}", ""]
        text = (node.get("content_template") or "").strip()
        if text:
            lines += [text, ""]
        transitions = [t for t in node.get("transitions", []) if t.get("to") in nodes]
        if transitions:
            lines += ["**Where do you go from here?**", ""]
            seen = set()
            for transition in transitions:
                target = transition["to"]
                if target in seen:
                    continue
                seen.add(target)
                label = transition_label(target, transition)
                lines.append(f"- [{label}](#{anchor(target)})")
            lines.append("")
    return lines


def main() -> None:
    act1 = json.loads(ACT1.read_text(encoding="utf-8"))
    act2 = json.loads(ACT2.read_text(encoding="utf-8"))
    lines = [
        "# The Voyd Terminal",
        "",
        "*A living branching narrative. Start anywhere. Follow a choice. The newest accepted frontier remains part of the same readable ancestry.*",
        "",
        "**[Reader portal / current frontier →](START_HERE.md)**",
        "",
        "---",
        "",
    ]
    lines += render_act1(act1["nodes"])
    lines += ["---", ""]
    lines += render_act2(act2["nodes"])
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
