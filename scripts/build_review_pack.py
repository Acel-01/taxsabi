#!/usr/bin/env python3
"""Build an HTML review pack for the verified SFT conversations.

Produces data/sft_review/review_pack_v1.html: a self-contained page (no
dependencies) where each conversation is a card with Approve / Reject /
Annotate buttons, a note field, filters, progress persistence, and an export
button that produces the flag list to send back.

Usage:
    uv run python scripts/build_review_pack.py
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "data" / "sft_verified"
OUT = ROOT / "data" / "sft_review" / "review_pack_v1.html"

LAYERS = {
    "layer_a": "A - English bulk",
    "layer_b": "B - English coaching",
    "layer_c": "C - Pidgin",
}

# Stratified sample sizes by layer and type (total 100).
SAMPLE = {
    "layer_a": {
        "accumulate_compute": 16,
        "counterfactual": 14,
        "correction": 8,
        "clarify_compute": 7,
        "topic_shift": 7,
        "scope_decline": 8,
    },
    "layer_b": {"coaching_discovery": 6, "coaching_savings": 6, "coaching_sequencing": 5},
    "layer_c": {
        "accumulate_compute": 9,
        "counterfactual": 6,
        "correction": 3,
        "clarify_compute": 2,
        "scope_decline": 3,
    },
}

CRITERIA = [
    ("User phrasing", "Does it sound like a real person, or a template?"),
    ("Assistant tone", "Concise, direct, coach-like - not preachy, robotic, or over-explaining?"),
    ("Coaching (layer B)", "Does it ask before asserting reliefs? Is the sequencing advice sensible?"),
    ("Pidgin (layer C)", "Authentic Lagos Pidgin, or English with Pidgin words sprinkled in?"),
    ("Policy / taste", "Anything you never want the model to say or do?"),
    ("Coverage gaps", "Scenarios you know matter that are missing entirely?"),
]


def load_layer(layer: str) -> list[dict]:
    path = VERIFIED / f"{layer}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def stratified_sample() -> list[dict]:
    selected: list[list[dict]] = []
    rng = random.Random(7)
    for layer, type_counts in SAMPLE.items():
        rows = load_layer(layer)
        by_type: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_type[row["type"]].append(row)
        for conv_type, count in type_counts.items():
            pool = sorted(by_type.get(conv_type, []), key=lambda r: r["id"])
            if not pool:
                continue
            step = max(1, len(pool) // count)
            picks = [pool[(i * step) % len(pool)] for i in range(count)]
            # de-duplicate while keeping order
            seen = set()
            unique = []
            for pick in picks:
                if pick["id"] not in seen:
                    seen.add(pick["id"])
                    unique.append({"layer": layer, **pick})
            selected.append(unique)
    # interleave so the review does not read one type in a long block
    interleaved: list[dict] = []
    index = 0
    while any(index < len(group) for group in selected):
        for group in selected:
            if index < len(group):
                interleaved.append(group[index])
        index += 1
    rng.shuffle(interleaved) if False else None
    return interleaved


def render_conversation(item: dict, number: int) -> str:
    turns = "".join(
        f'<div class="turn {turn["role"]}"><span class="role">{turn["role"]}</span>'
        f'<div class="content">{turn["content"]}</div></div>'
        for turn in item["turns"]
    )
    language = "Pidgin" if item.get("language") == "pcm" else "English"
    return f"""
    <article class="card" id="card-{number}" data-layer="{item['layer']}" data-type="{item['type']}">
      <header class="card-head">
        <div class="meta">
          <span class="num">#{number}</span>
          <span class="badge layer">{LAYERS[item['layer']]}</span>
          <span class="badge type">{item['type']}</span>
          <span class="badge lang">{language}</span>
          <span class="scenario">{item['id']} &middot; {item['scenario_id']}</span>
        </div>
        <div class="verdict-buttons">
          <button class="approve" data-verdict="approve">Approve</button>
          <button class="reject" data-verdict="reject">Reject</button>
          <button class="annotate" data-verdict="annotate">Annotate</button>
        </div>
      </header>
      <div class="transcript">{turns}</div>
      <input class="note" type="text" placeholder="note (only needed for reject / annotate)">
    </article>"""


def build_html(items: list[dict]) -> str:
    cards = "\n".join(render_conversation(item, i + 1) for i, item in enumerate(items))
    data = json.dumps(
        [
            {
                "n": i + 1,
                "id": item["id"],
                "layer": item["layer"],
                "type": item["type"],
                "language": item.get("language"),
            }
            for i, item in enumerate(items)
        ],
        ensure_ascii=False,
    ).replace("</", "<\\/")
    criteria = "".join(f"<li><b>{name}:</b> {text}</li>" for name, text in CRITERIA)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SFT Review Pack v1</title>
<style>
  :root {{
    --bg: #f7f7f5; --card: #ffffff; --ink: #1c1d21; --muted: #6b6f76;
    --line: #e3e3df; --accent: #0a6b4f; --reject: #b3261e; --annotate: #9a6700;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink);
    font: 15px/1.55 -apple-system, "Segoe UI", Roboto, Ubuntu, sans-serif; }}
  .wrap {{ max-width: 900px; margin: 0 auto; padding: 20px 16px 120px; }}
  h1 {{ font-size: 22px; margin: 0 0 6px; }}
  .intro {{ color: var(--muted); margin-bottom: 12px; }}
  .criteria {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    padding: 12px 16px 12px 34px; margin-bottom: 18px; }}
  .criteria li {{ margin: 3px 0; }}
  .toolbar {{ position: sticky; top: 0; z-index: 5; display: flex; gap: 8px; align-items: center;
    flex-wrap: wrap; background: var(--bg); padding: 10px 0; border-bottom: 1px solid var(--line); }}
  .toolbar button, .filters button {{ border: 1px solid var(--line); background: var(--card);
    color: var(--ink); padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; }}
  .toolbar button.primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .progress {{ margin-left: auto; color: var(--muted); font-size: 13px; }}
  .filters {{ display: flex; gap: 6px; flex-wrap: wrap; margin: 14px 0; }}
  .filters button.active {{ border-color: var(--ink); font-weight: 600; }}
  .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: 14px 16px; margin-bottom: 16px; }}
  .card.verdict-approve {{ border-left: 5px solid var(--accent); }}
  .card.verdict-reject {{ border-left: 5px solid var(--reject); }}
  .card.verdict-annotate {{ border-left: 5px solid var(--annotate); }}
  .card.hidden {{ display: none; }}
  .card-head {{ display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }}
  .meta {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; font-size: 12px; }}
  .num {{ font-weight: 700; font-size: 14px; }}
  .badge {{ border-radius: 999px; padding: 2px 9px; background: #eef0ee; color: #3c4046; }}
  .badge.layer {{ background: #e7f0ec; color: #0a5c44; }}
  .scenario {{ color: var(--muted); }}
  .verdict-buttons button {{ border: 1px solid var(--line); background: #fff; border-radius: 8px;
    padding: 5px 11px; cursor: pointer; font-size: 13px; }}
  .verdict-buttons button.selected.approve {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .verdict-buttons button.selected.reject {{ background: var(--reject); color: #fff; border-color: var(--reject); }}
  .verdict-buttons button.selected.annotate {{ background: var(--annotate); color: #fff; border-color: var(--annotate); }}
  .transcript {{ display: flex; flex-direction: column; gap: 8px; }}
  .turn {{ display: grid; grid-template-columns: 78px 1fr; gap: 10px; }}
  .role {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); padding-top: 2px; }}
  .turn.assistant .content {{ background: #f2f6f4; border-radius: 8px; padding: 8px 10px; }}
  .turn.user .content {{ padding: 2px 0; }}
  .note {{ width: 100%; margin-top: 10px; border: 1px solid var(--line); border-radius: 8px;
    padding: 7px 10px; font: inherit; }}
  .note:focus {{ outline: 2px solid #cfe3da; }}
  .export {{ position: fixed; left: 0; right: 0; bottom: 0; background: var(--card);
    border-top: 1px solid var(--line); padding: 10px 16px; display: none; }}
  .export.show {{ display: block; }}
  .export textarea {{ width: 100%; height: 130px; font: 12px/1.4 monospace; border: 1px solid var(--line);
    border-radius: 8px; padding: 8px; }}
  .export .row {{ display: flex; gap: 8px; align-items: center; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>SFT Review Pack v1</h1>
  <p class="intro">Flag only what bothers you &mdash; silence means approved. Numbers and format are
  already engine-verified; this pass is about taste and coverage. Progress is saved in this browser.</p>
  <ul class="criteria">{criteria}</ul>

  <div class="toolbar">
    <button class="primary" id="export-btn">Export flags</button>
    <button id="reset-btn">Reset</button>
    <span class="progress" id="progress"></span>
  </div>
  <div class="filters" id="filters">
    <button data-filter="all" class="active">All</button>
    <button data-filter="pending">Pending</button>
    <button data-filter="layer_a">Layer A</button>
    <button data-filter="layer_b">Layer B</button>
    <button data-filter="layer_c">Layer C</button>
    <button data-filter="reject">Rejected</button>
    <button data-filter="annotate">Annotated</button>
  </div>

  <div id="cards">
{cards}
  </div>
</div>

<div class="export" id="export-panel">
  <div class="row">
    <strong>Copy this back to the agent:</strong>
    <button id="copy-btn">Copy</button>
    <button id="close-btn">Close</button>
  </div>
  <textarea id="export-text" readonly></textarea>
</div>

<script>
const META = {data};
const KEY = "sft_review_v1";
let state = JSON.parse(localStorage.getItem(KEY) || "{{}}");

function save() {{ try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}} }}
function verdictOf(n) {{ return (state[n] && state[n].verdict) || null; }}

function updateProgress() {{
  let a = 0, r = 0, t = 0, p = 0;
  META.forEach(m => {{
    const v = verdictOf(m.n);
    if (v === "approve") a++; else if (v === "reject") r++; else if (v === "annotate") t++; else p++;
  }});
  document.getElementById("progress").textContent =
    `Reviewed ${{META.length - p}}/${{META.length}} - approved ${{a}}, rejected ${{r}}, annotate ${{t}}, pending ${{p}}`;
}}

document.querySelectorAll(".card").forEach(card => {{
  const n = Number(card.id.replace("card-", ""));
  const buttons = card.querySelectorAll(".verdict-buttons button");
  const note = card.querySelector(".note");
  const saved = state[n] || {{}};
  note.value = saved.note || "";
  if (saved.verdict) {{
    card.classList.add("verdict-" + saved.verdict);
    buttons.forEach(b => {{ if (b.dataset.verdict === saved.verdict) b.classList.add("selected"); }});
  }}
  buttons.forEach(btn => btn.addEventListener("click", () => {{
    const v = btn.dataset.verdict;
    const current = verdictOf(n);
    const next = current === v ? null : v;
    state[n] = {{ verdict: next, note: note.value }};
    buttons.forEach(b => b.classList.remove("selected"));
    card.classList.remove("verdict-approve", "verdict-reject", "verdict-annotate");
    if (next) {{
      btn.classList.add("selected");
      card.classList.add("verdict-" + next);
    }}
    save(); updateProgress();
  }}));
  note.addEventListener("change", () => {{
    state[n] = {{ verdict: verdictOf(n), note: note.value }};
    save();
  }});
}});

document.getElementById("filters").addEventListener("click", (event) => {{
  const button = event.target.closest("button");
  if (!button) return;
  document.querySelectorAll("#filters button").forEach(b => b.classList.remove("active"));
  button.classList.add("active");
  const filter = button.dataset.filter;
  META.forEach(m => {{
    const card = document.getElementById("card-" + m.n);
    const v = verdictOf(m.n);
    let show = true;
    if (filter === "pending") show = !v;
    else if (filter === "layer_a" || filter === "layer_b" || filter === "layer_c") show = m.layer === filter;
    else if (filter === "reject" || filter === "annotate") show = v === filter;
    card.classList.toggle("hidden", !show);
  }});
}});

document.getElementById("export-btn").addEventListener("click", () => {{
  const lines = [];
  META.forEach(m => {{
    const entry = state[m.n];
    if (entry && (entry.verdict === "reject" || entry.verdict === "annotate")) {{
      lines.push(`#${{m.n}} [${{m.layer}}/${{m.type}} ${{m.id}}] ${{entry.verdict.toUpperCase()}}: ${{entry.note || "(no note)"}}`);
    }}
  }});
  const vcounts = {{ approve: 0, reject: 0, annotate: 0, pending: 0 }};
  META.forEach(m => {{ const v = verdictOf(m.n) || "pending"; vcounts[v]++; }});
  const header = `SFT REVIEW PACK v1 - reviewed ${{META.length - vcounts.pending}}/${{META.length}} ` +
    `(approved ${{vcounts.approve}}, rejected ${{vcounts.reject}}, annotate ${{vcounts.annotate}}, pending ${{vcounts.pending}})`;
  const text = header + "\\n" + lines.join("\\n");
  document.getElementById("export-text").value = text;
  document.getElementById("export-panel").classList.add("show");
  document.getElementById("export-text").select();
}});

document.getElementById("copy-btn").addEventListener("click", () => {{
  const area = document.getElementById("export-text");
  area.select(); document.execCommand("copy");
}});
document.getElementById("close-btn").addEventListener("click", () => {{
  document.getElementById("export-panel").classList.remove("show");
}});
document.getElementById("reset-btn").addEventListener("click", () => {{
  if (!confirm("Clear all verdicts and notes?")) return;
  state = {{}}; save();
  document.querySelectorAll(".card").forEach(card => {{
    card.classList.remove("verdict-approve", "verdict-reject", "verdict-annotate");
    card.querySelector(".note").value = "";
    card.querySelectorAll(".verdict-buttons button").forEach(b => b.classList.remove("selected"));
  }});
  updateProgress();
}});

updateProgress();
</script>
</body>
</html>
"""


def main() -> None:
    items = stratified_sample()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(items))
    composition: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in items:
        composition[item["layer"]][item["type"]] += 1
    print(f"wrote {len(items)} conversations -> {OUT}")
    for layer, counts in composition.items():
        print(f"  {layer}: {dict(counts)}")


if __name__ == "__main__":
    main()
