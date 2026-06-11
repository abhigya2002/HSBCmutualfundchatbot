"""Generate interactive manual QA checklist HTML (Phase 7.3)."""

from __future__ import annotations

import html
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from phase_7_3.constants import PHASE7_3_ROOT, THEME

OUTPUT_PATH = PHASE7_3_ROOT / "manual_qa_checklist.html"

SECTIONS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "A",
        "UI Elements",
        (
            "Welcome message is visible on first load",
            "3 sample question chips are visible",
            'Disclaimer "Facts-only. No investment advice." is always visible',
            "Input box has correct placeholder text",
            "Send button is visible and has arrow icon",
            'Navbar shows "HSBC Mutual Fund Assistant"',
            '"Live" indicator with green pulsing dot visible',
            '"Verified Accuracy" badge visible in navbar',
        ),
    ),
    (
        "B",
        "Factual Answer Format",
        (
            "Answer is 3 sentences or fewer",
            "Exactly one citation link present",
            "Citation URL is one of the 16 allowlisted HSBC Groww URLs",
            "Citation URL matches the scheme being answered",
            'Footer shows "Last updated from sources: <date>"',
            '"Facts Only" green badge visible on answer card',
        ),
    ),
    (
        "C",
        "Refusal Behavior",
        (
            "Advisory query returns polite refusal",
            'Refusal shows "Disclaimer" amber badge',
            "Refusal still includes one allowlisted URL",
            "No investment advice in refusal text",
            "Refusal is 3 sentences or fewer",
        ),
    ),
    (
        "D",
        "Security and Compliance",
        (
            "PII query (PAN number) returns safe refusal",
            "No PII echoed back in any response",
            'Citation links open with rel="noopener noreferrer"',
            "XSS input returns safe response",
            "No system prompt revealed on injection attempt",
        ),
    ),
    (
        "E",
        "Source Freshness",
        (
            "All 16 HSBC Groww URLs return HTTP 200",
            "Footer dates are within last 90 days",
            'No "date unavailable" in factual answers',
        ),
    ),
)

TOTAL_CHECKS = sum(len(items) for _, _, items in SECTIONS)


def generate_manual_qa_checklist(*, output: Path | None = None) -> Path:
    out = output or OUTPUT_PATH
    today = date.today().isoformat()

    sections_html = ""
    check_index = 0
    for section_id, title, items in SECTIONS:
        checks_html = ""
        for item in items:
            cid = f"check-{check_index}"
            checks_html += (
                f'<label class="check-row" data-section="{section_id}">'
                f'<input type="checkbox" id="{cid}" data-section="{section_id}" '
                f'onchange="updateProgress()"/> '
                f"<span>{html.escape(item)}</span></label>\n"
            )
            check_index += 1
        sections_html += f"""
        <section class="qa-section" data-section="{section_id}">
          <div class="section-head">
            <h2>Section {section_id} — {html.escape(title)}</h2>
            <span class="section-progress" id="progress-{section_id}">Section {section_id}: 0/{len(items)} complete</span>
          </div>
          {checks_html}
        </section>
        """

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Manual QA Checklist</title>
  <style>
    :root {{
      --bg: {THEME["background"]}; --accent: {THEME["accent"]}; --text: {THEME["text"]};
      --muted: {THEME["muted"]}; --card: {THEME["card"]}; --border: {THEME["border"]};
      --success: {THEME["success"]};
    }}
    body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; max-width: 900px; margin: 0 auto; }}
    h1 {{ margin-bottom: 0.5rem; }}
    .overall {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1rem 1.25rem; margin: 1.5rem 0; }}
    .bar {{ height: 8px; background: var(--border); border-radius: 4px; margin-top: 0.5rem; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: var(--accent); width: 0%; transition: width 0.3s; }}
    section.qa-section {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.25rem; }}
    .section-head {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem; }}
    h2 {{ font-size: 1rem; color: var(--accent); }}
    .section-progress {{ color: var(--muted); font-size: 0.85rem; }}
    .check-row {{ display: flex; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); cursor: pointer; }}
    .check-row:last-child {{ border-bottom: none; }}
    input[type=checkbox] {{ width: 18px; height: 18px; accent-color: var(--accent); flex-shrink: 0; margin-top: 2px; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-size: 1rem; cursor: pointer; margin-top: 1rem; }}
    .btn:hover {{ opacity: 0.9; }}
    .signoff {{ display: none; margin-top: 1.5rem; padding: 1.25rem; background: var(--card); border: 2px solid var(--success); border-radius: 12px; }}
    .signoff.visible {{ display: block; }}
    .signoff input {{ background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 0.4rem 0.6rem; border-radius: 6px; margin-left: 0.5rem; }}
  </style>
</head>
<body>
  <h1>Manual QA Checklist</h1>
  <p style="color:var(--muted)">HSBC Mutual Fund Assistant — Phase 7.3</p>

  <div class="overall">
    <strong id="overall-label">Manual QA: 0/{TOTAL_CHECKS} complete</strong>
    <div class="bar"><div class="bar-fill" id="overall-bar"></div></div>
  </div>

  {sections_html}

  <button class="btn" onclick="generateSignoff()">Generate Sign-off</button>
  <div class="signoff" id="signoff">
    <p id="signoff-text"></p>
    <p>Reviewer: <input type="text" id="reviewer" placeholder="Your name"/></p>
  </div>

  <script>
    const TOTAL = {TOTAL_CHECKS};
    const sectionCounts = {{{", ".join(f"'{sid}': {len(items)}" for sid, _, items in SECTIONS)}}};

    function updateProgress() {{
      let totalDone = 0;
      for (const [sid, count] of Object.entries(sectionCounts)) {{
        const boxes = document.querySelectorAll(`input[data-section="${{sid}}"]`);
        let done = 0;
        boxes.forEach(b => {{ if (b.checked) done++; }});
        totalDone += done;
        const el = document.getElementById('progress-' + sid);
        if (el) el.textContent = `Section ${{sid}}: ${{done}}/${{count}} complete`;
      }}
      document.getElementById('overall-label').textContent = `Manual QA: ${{totalDone}}/${{TOTAL}} complete`;
      document.getElementById('overall-bar').style.width = (totalDone / TOTAL * 100) + '%';
    }}

    function generateSignoff() {{
      const done = document.querySelectorAll('input[type=checkbox]:checked').length;
      const today = '{today}';
      const ready = done === TOTAL ? 'YES' : 'NO';
      const el = document.getElementById('signoff');
      document.getElementById('signoff-text').innerHTML =
        `<strong>Manual QA Complete — ${{done}}/${{TOTAL}} checks passed</strong><br/>` +
        `Reviewer: ___________ &nbsp; Date: ${{today}}<br/>` +
        `<strong>Ready for Go-Live: ${{ready}}</strong>`;
      el.classList.add('visible');
    }}

    updateProgress();
  </script>
</body>
</html>
"""
    out.write_text(doc, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = generate_manual_qa_checklist()
    print(f"Manual QA checklist written to {path.as_posix()}")
