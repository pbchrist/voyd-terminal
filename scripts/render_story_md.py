#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ACT1 = ROOT / "data" / "act1_nodes.json"
ACT2 = ROOT / "data" / "story_graph.json"
OUT = ROOT / "STORY.md"


def anchor(value: str) -> str:
    return value.lower().replace(".", "").replace("_", "-").replace(" ", "-")


def title_for(node_id: str, node: dict) -> str:
    label = node.get("label") or node.get("type") or node_id
    return label.replace("_", " ").title()


def render_act1(nodes: dict) -> list[str]:
    lines = ["## Act I — The Threshold", ""]
    for node_id, node in nodes.items():
        lines += [f'<a id="{anchor(node_id)}"></a>', f"### {title_for(node_id, node)}", ""]
        text = (node.get("text") or "").strip()
        if text:
            lines += [text, ""]
        choices = node.get("choices", [])
        if choices:
            lines += ["**Choose:**", ""]
            for choice in choices:
                target = choice.get("next", "")
                label = choice.get("label", target)
                if target == "ACT2":
                    lines.append(f"- **{label}** → continue to Act II")
                else:
                    lines.append(f"- [{label}](#{anchor(target)})")
            lines.append("")
    return lines

def render_act2(nodes: dict) -> list[str]:
    lines = ["## Act II — The Live Bargain", ""]
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
        transitions = node.get("transitions", [])
        if transitions:
            lines += ["**The story can move toward:**", ""]
            for transition in transitions:
                target = transition.get("to")
                condition = transition.get("condition", "continue")
                if target and target in nodes:
                    lines.append(f"- [{condition}](#{anchor(target)})")
            lines.append("")
    return lines

def main() -> None:
    act1 = json.loads(ACT1.read_text(encoding="utf-8"))
    act2 = json.loads(ACT2.read_text(encoding="utf-8"))
    lines = [
        "# The Voyd Terminal",
        "",
        "*A living branching story. Read it like a reader; choose a path when the story asks you to.*",
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
