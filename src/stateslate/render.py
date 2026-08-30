"""Deterministic StateSlate report renderers."""

# ruff: noqa: E501 -- standalone report templates keep readable HTML and CSS lines

from __future__ import annotations

import csv
import io
import json
from html import escape
from typing import Any

from stateslate import __version__
from stateslate.compiler import Compilation, Reference, ShootAction, ShootScene

ARTIFACT_NAMES = {
    "continuity.json",
    "report.html",
    "reset-checklist.md",
    "shoot-plan.csv",
    "timeline.svg",
}


def _state_map(states: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return dict(states)


def _report_data(compilation: Compilation) -> dict[str, Any]:
    project = compilation.timeline.project
    return {
        "schema_version": 1,
        "generator": {"name": "stateslate", "version": __version__},
        "project": {"title": project.title},
        "summary": {
            "scene_count": compilation.summary.scene_count,
            "track_count": compilation.summary.track_count,
            "prepare_count": compilation.summary.prepare_count,
            "reset_count": compilation.summary.reset_count,
            "high_risk_count": compilation.summary.high_risk_count,
            "medium_risk_count": compilation.summary.medium_risk_count,
        },
        "tracks": [
            {
                "id": track.id,
                "label": track.label,
                "category": track.category,
                "initial": track.initial,
            }
            for track in project.tracks
        ],
        "story_scenes": [
            {
                "id": scene.id,
                "title": scene.title,
                "story_order": scene.story_order,
                "shoot": {"day": scene.shoot.day, "order": scene.shoot.order},
                "entry_states": _state_map(scene.entry_states),
                "exit_states": _state_map(scene.exit_states),
                "transitions": [
                    {
                        "track": transition.track,
                        "from": transition.from_state,
                        "to": transition.to_state,
                        "note": transition.note,
                    }
                    for transition in scene.transitions
                ],
            }
            for scene in compilation.timeline.scenes
        ],
        "shoot_scenes": [
            {
                "id": scene.id,
                "title": scene.title,
                "story_order": scene.story_order,
                "shoot": {"day": scene.shoot.day, "order": scene.shoot.order},
                "setup_states": _state_map(scene.setup_states),
                "exit_states": _state_map(scene.exit_states),
                "actions": [
                    {
                        "kind": action.kind,
                        "track": action.track,
                        "from": action.from_state,
                        "to": action.to_state,
                        "source_scene": action.source_scene,
                    }
                    for action in scene.actions
                ],
                "references": [
                    {
                        "track": reference.track,
                        "status": reference.status,
                        "source_scene": reference.source_scene,
                        "day_gap": reference.day_gap,
                    }
                    for reference in scene.references
                ],
            }
            for scene in compilation.shoot_scenes
        ],
        "risks": [
            {
                "code": risk.code,
                "severity": risk.severity,
                "scene": risk.scene,
                "track": risk.track,
                "source_scene": risk.source_scene,
                "day_gap": risk.day_gap,
            }
            for risk in compilation.risks
        ],
    }


def _render_json(compilation: Compilation) -> str:
    return (
        json.dumps(_report_data(compilation), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )


def _csv_safe(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def _action_for(scene: ShootScene, track: str) -> ShootAction | None:
    return next((action for action in scene.actions if action.track == track), None)


def _reference_for(scene: ShootScene, track: str) -> Reference:
    return next(reference for reference in scene.references if reference.track == track)


def _render_csv(compilation: Compilation) -> str:
    track_metadata = {track.id: track for track in compilation.timeline.project.tracks}
    risk_codes = {
        (scene.id, track): ";".join(
            risk.code
            for risk in compilation.risks
            if risk.scene == scene.id and risk.track == track
        )
        for scene in compilation.shoot_scenes
        for track, _state in scene.setup_states
    }
    fields = [
        "shoot_day",
        "shoot_order",
        "scene_id",
        "scene_title",
        "story_order",
        "track_id",
        "track_label",
        "category",
        "setup_state",
        "exit_state",
        "action_kind",
        "from_state",
        "reference_status",
        "reference_scene",
        "day_gap",
        "risk_codes",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for scene in compilation.shoot_scenes:
        exits = dict(scene.exit_states)
        for track, setup_state in scene.setup_states:
            metadata = track_metadata[track]
            action = _action_for(scene, track)
            reference = _reference_for(scene, track)
            row = {
                "shoot_day": scene.shoot.day,
                "shoot_order": scene.shoot.order,
                "scene_id": scene.id,
                "scene_title": scene.title,
                "story_order": scene.story_order,
                "track_id": track,
                "track_label": metadata.label,
                "category": metadata.category,
                "setup_state": setup_state,
                "exit_state": exits[track],
                "action_kind": action.kind if action else "confirm",
                "from_state": action.from_state if action else setup_state,
                "reference_status": reference.status,
                "reference_scene": reference.source_scene,
                "day_gap": reference.day_gap,
                "risk_codes": risk_codes[(scene.id, track)],
            }
            writer.writerow({key: _csv_safe(value) for key, value in row.items()})
    return stream.getvalue()


def _md(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _code(value: str) -> str:
    return "`" + value.replace("`", "\\`") + "`"


def _reference_text(reference: Reference) -> str:
    if reference.status == "initial":
        return "initial state"
    return f"{reference.status}: {reference.source_scene} ({reference.day_gap} day gap)"


def _render_markdown(compilation: Compilation) -> str:
    project = compilation.timeline.project
    lines = [
        f"# {_md(project.title)} — reset checklist",
        "",
        (
            f"Scenes: **{compilation.summary.scene_count}** · "
            f"prepare: **{compilation.summary.prepare_count}** · "
            f"reset: **{compilation.summary.reset_count}** · "
            f"high risks: **{compilation.summary.high_risk_count}** · "
            f"medium risks: **{compilation.summary.medium_risk_count}**"
        ),
        "",
    ]
    metadata = {track.id: track for track in project.tracks}
    for scene in compilation.shoot_scenes:
        lines.extend(
            [
                f"## Day {scene.shoot.day} / {scene.shoot.order} — {scene.id} — {_md(scene.title)}",
                "",
            ]
        )
        if scene.actions:
            for action in scene.actions:
                if action.kind == "prepare":
                    lines.append(f"- Prepare {_code(action.track)} as {_code(action.to_state)}.")
                else:
                    lines.append(
                        f"- Reset {_code(action.track)}: {_code(action.from_state or '')} → "
                        f"{_code(action.to_state)} (after {action.source_scene})."
                    )
        else:
            lines.append("- No state changes from the previous scheduled use.")
        lines.extend(
            [
                "",
                "| Track | Label | Category | Setup | Exit | Reference |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        exits = dict(scene.exit_states)
        for track, state in scene.setup_states:
            info = metadata[track]
            reference = _reference_for(scene, track)
            lines.append(
                f"| {_code(track)} | {_md(info.label)} | {_md(info.category)} | "
                f"{_code(state)} | {_code(exits[track])} | {_md(_reference_text(reference))} |"
            )
        scene_risks = [risk for risk in compilation.risks if risk.scene == scene.id]
        if scene_risks:
            lines.extend(["", "Risks:"])
            for risk in scene_risks:
                lines.append(
                    f"- **{risk.severity.upper()} {risk.code}** — {_code(risk.track)} "
                    f"references {risk.source_scene} across {risk.day_gap} shoot day(s)."
                )
        lines.append("")
    lines.extend(
        [
            "> StateSlate compiles declared states. Confirm every setup against the approved ",
            "> continuity notes and on-set reference material.",
        ]
    )
    return "\n".join(lines) + "\n"


def _scene_card(x: int, y: int, heading: str, scene_id: str, title: str, accent: str) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="500" height="78" rx="14" fill="#ffffff" '
            f'stroke="{accent}" stroke-width="2"/>',
            f'<text x="{x + 20}" y="{y + 28}" class="meta">{escape(heading)}</text>',
            f'<text x="{x + 20}" y="{y + 56}" class="scene">'
            f"{escape(scene_id)} · {escape(title)}</text>",
        ]
    )


def _render_svg(compilation: Compilation) -> str:
    count = max(len(compilation.timeline.scenes), len(compilation.shoot_scenes))
    height = 150 + count * 100
    project_title = escape(compilation.timeline.project.title)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'viewBox="0 0 1120 {height}" width="1120" height="{height}">',
        f"<title>StateSlate continuity timeline for {project_title}</title>",
        "<desc>Story order appears on the left and scheduled shoot order on the right.</desc>",
        "<style>",
        ".title{font:700 28px system-ui,sans-serif;fill:#17213b}",
        ".heading{font:700 15px system-ui,sans-serif;letter-spacing:.12em;fill:#59637d}",
        ".meta{font:600 13px system-ui,sans-serif;fill:#59637d}",
        ".scene{font:700 17px system-ui,sans-serif;fill:#17213b}",
        "</style>",
        f'<rect width="1120" height="{height}" fill="#f4f1ea"/>',
        f'<text x="40" y="48" class="title">{project_title}</text>',
        '<text x="40" y="84" class="heading">STORY ORDER · STATE AUTHORITY</text>',
        '<text x="580" y="84" class="heading">SHOOT ORDER · RESET PLAN</text>',
    ]
    risk_scenes = {risk.scene for risk in compilation.risks}
    for index, story_scene in enumerate(compilation.timeline.scenes):
        parts.append(
            _scene_card(
                40,
                105 + index * 100,
                f"Story {story_scene.story_order}",
                story_scene.id,
                story_scene.title,
                "#635bff",
            )
        )
    for index, shoot_scene in enumerate(compilation.shoot_scenes):
        accent = "#d1495b" if shoot_scene.id in risk_scenes else "#1d8a72"
        parts.append(
            _scene_card(
                580,
                105 + index * 100,
                f"Day {shoot_scene.shoot.day} · order {shoot_scene.shoot.order}",
                shoot_scene.id,
                shoot_scene.title,
                accent,
            )
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _render_html(compilation: Compilation, svg: str) -> str:
    title = escape(compilation.timeline.project.title)
    summary = compilation.summary
    risk_rows = (
        "".join(
            "<tr>"
            f'<td><span class="pill {risk.severity}">{risk.severity}</span></td>'
            f"<td>{escape(risk.code)}</td><td>{escape(risk.scene)}</td>"
            f"<td>{escape(risk.track)}</td><td>{escape(risk.source_scene)}</td>"
            f"<td>{risk.day_gap}</td></tr>"
            for risk in compilation.risks
        )
        or '<tr><td colspan="6">No reference risks at this threshold.</td></tr>'
    )
    metadata = {track.id: track for track in compilation.timeline.project.tracks}
    scene_sections: list[str] = []
    for scene in compilation.shoot_scenes:
        exits = dict(scene.exit_states)
        action_items = (
            "".join(
                f"<li><strong>{escape(action.kind.title())}</strong> "
                f"<code>{escape(action.track)}</code>: "
                f"{escape(action.from_state or 'unprepared')} → {escape(action.to_state)}</li>"
                for action in scene.actions
            )
            or "<li>No state changes from the previous scheduled use.</li>"
        )
        state_rows = "".join(
            "<tr>"
            f"<td><code>{escape(track)}</code></td>"
            f"<td>{escape(metadata[track].label)}</td>"
            f"<td>{escape(state)}</td><td>{escape(exits[track])}</td>"
            f"<td>{escape(_reference_text(_reference_for(scene, track)))}</td>"
            "</tr>"
            for track, state in scene.setup_states
        )
        scene_sections.append(
            f'<section class="scene-card"><header><span>Day {scene.shoot.day} / '
            f"{scene.shoot.order}</span><h3>{escape(scene.id)} · {escape(scene.title)}</h3>"
            f"<small>Story position {scene.story_order}</small></header>"
            f'<ul class="actions">{action_items}</ul><div class="table-wrap"><table>'
            "<thead><tr><th>Track</th><th>Label</th><th>Setup</th><th>Exit</th>"
            f"<th>Reference</th></tr></thead><tbody>{state_rows}</tbody></table></div></section>"
        )
    inline_svg = svg.removesuffix("\n")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · StateSlate continuity report</title>
<style>
:root{{--ink:#17213b;--muted:#667085;--paper:#f4f1ea;--card:#fff;--violet:#635bff;--red:#d1495b;--amber:#b26a00}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:48px 24px 72px}}h1{{font-size:clamp(2.2rem,7vw,5rem);line-height:.95;margin:.25em 0}}
.eyebrow{{font-weight:800;letter-spacing:.16em;color:var(--violet)}}.lede{{max-width:760px;color:var(--muted);font-size:1.15rem}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:12px;margin:32px 0}}
.stat,.panel,.scene-card{{background:var(--card);border:1px solid #d8d3c7;border-radius:18px;box-shadow:0 8px 30px #17213b0d}}
.stat{{padding:18px}}.stat strong{{display:block;font-size:2rem}}.stat span,small{{color:var(--muted)}}
.panel{{padding:22px;margin:22px 0;overflow:hidden}}.panel svg{{width:100%;height:auto;display:block}}
.scene-card{{margin:18px 0;overflow:hidden}}.scene-card header{{padding:20px 22px;border-bottom:1px solid #ece8df}}
.scene-card header span{{font-weight:800;color:var(--violet)}}.scene-card h3{{margin:.2rem 0;font-size:1.35rem}}
.actions{{margin:18px 40px}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse}}
th,td{{padding:12px 14px;text-align:left;border-top:1px solid #ece8df;vertical-align:top}}th{{font-size:.8rem;letter-spacing:.08em;color:var(--muted)}}
code{{background:#f1efff;border-radius:5px;padding:.12em .35em}}.pill{{display:inline-block;border-radius:99px;padding:.2em .7em;font-weight:800;color:#fff}}
.pill.high{{background:var(--red)}}.pill.medium{{background:var(--amber)}}.caveat{{border-left:5px solid var(--violet);padding:12px 18px;background:#eeebff}}
@media print{{body{{background:#fff}}main{{padding:0}}.stat,.panel,.scene-card{{box-shadow:none;break-inside:avoid}}}}
</style>
</head>
<body><main>
<p class="eyebrow">STATESLATE · OFFLINE CONTINUITY COMPILER</p>
<h1>{title}</h1>
<p class="lede">Story-state authority projected into shoot-order preparations, resets, and reference risks. Generated deterministically from the reviewed project file.</p>
<section class="stats" aria-label="Compilation summary">
<div class="stat"><strong>{summary.scene_count}</strong><span>scenes</span></div>
<div class="stat"><strong>{summary.track_count}</strong><span>tracks</span></div>
<div class="stat"><strong>{summary.prepare_count}</strong><span>preparations</span></div>
<div class="stat"><strong>{summary.reset_count}</strong><span>resets</span></div>
<div class="stat"><strong>{summary.high_risk_count}</strong><span>high risks</span></div>
<div class="stat"><strong>{summary.medium_risk_count}</strong><span>medium risks</span></div>
</section>
<section class="panel" aria-labelledby="timeline-heading"><h2 id="timeline-heading">Two orders, one state authority</h2>{inline_svg}</section>
<section class="panel"><h2>Reference risks</h2><div class="table-wrap"><table><thead><tr><th>Severity</th><th>Code</th><th>Scene</th><th>Track</th><th>Source</th><th>Days</th></tr></thead><tbody>{risk_rows}</tbody></table></div></section>
<h2>Shoot-day reset plan</h2>
{"".join(scene_sections)}
<p class="caveat"><strong>Boundary:</strong> StateSlate compiles declared states. Confirm every setup against approved notes and on-set reference material; this report does not prove visual or physical continuity.</p>
</main></body></html>
"""


def render_artifacts(compilation: Compilation) -> dict[str, str]:
    """Render the complete report set from one compiled continuity model."""

    svg = _render_svg(compilation)
    artifacts = {
        "continuity.json": _render_json(compilation),
        "shoot-plan.csv": _render_csv(compilation),
        "reset-checklist.md": _render_markdown(compilation),
        "timeline.svg": svg,
        "report.html": _render_html(compilation, svg),
    }
    assert set(artifacts) == ARTIFACT_NAMES
    return artifacts
