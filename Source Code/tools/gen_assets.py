"""Generate README visuals (docs/banner.svg, docs/overlay.svg).

Pure-SVG so they render crisply on GitHub (no external fonts / no filters that
GitHub's image proxy would strip)."""

import math
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
DOCS.mkdir(exist_ok=True)

FONT = "'Segoe UI', system-ui, -apple-system, Roboto, Arial, sans-serif"


def wave_bars(n, x0, cy, pitch, min_h, max_h, color, envelope=True, phase=0.3):
    out = []
    for i in range(n):
        env = math.sin(math.pi * (i + 0.5) / n) if envelope else 1.0
        osc = 0.45 + 0.55 * abs(math.sin(phase + i * 0.7))
        h = max(min_h, (min_h + (max_h - min_h) * osc) * (0.35 + 0.65 * env))
        x = x0 + i * pitch
        w = pitch * 0.5
        out.append(
            f'<rect x="{x:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" '
            f'height="{h:.1f}" rx="{w / 2:.1f}" fill="{color}"/>'
        )
    return "\n      ".join(out)


def mic_emblem(s):
    """White microphone glyph sized to an s x s box."""
    cx = s * 0.5
    return f"""
      <rect x="{s*0.385:.1f}" y="{s*0.20:.1f}" width="{s*0.23:.1f}" height="{s*0.36:.1f}" rx="{s*0.115:.1f}" fill="#ffffff"/>
      <path d="M{s*0.31:.1f} {s*0.45:.1f} a{s*0.19:.1f} {s*0.18:.1f} 0 0 0 {s*0.38:.1f} 0" fill="none" stroke="#ffffff" stroke-width="{s*0.05:.1f}" stroke-linecap="round"/>
      <line x1="{cx:.1f}" y1="{s*0.63:.1f}" x2="{cx:.1f}" y2="{s*0.76:.1f}" stroke="#ffffff" stroke-width="{s*0.05:.1f}" stroke-linecap="round"/>
      <line x1="{s*0.40:.1f}" y1="{s*0.78:.1f}" x2="{s*0.60:.1f}" y2="{s*0.78:.1f}" stroke="#ffffff" stroke-width="{s*0.05:.1f}" stroke-linecap="round"/>"""


def banner():
    W, H = 1200, 340
    bars_bg = wave_bars(60, 60, 300, 19, 6, 150, "#1E2A44", envelope=True, phase=1.1)
    bars_fg = wave_bars(44, 282, 300, 11, 6, 64, "url(#bars)", envelope=True, phase=0.5)
    return f"""<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0B1220"/><stop offset="1" stop-color="#151F35"/>
    </linearGradient>
    <linearGradient id="emblem" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#60A5FA"/><stop offset="1" stop-color="#2563EB"/>
    </linearGradient>
    <linearGradient id="bars" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7DD3FC"/><stop offset="1" stop-color="#2563EB"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="{W}" height="{H}" rx="28" fill="url(#bg)"/>
  <g opacity="0.5">
      {bars_bg}
  </g>
  <ellipse cx="158" cy="150" rx="135" ry="135" fill="#3B82F6" opacity="0.10"/>
  <g transform="translate(92,84)">
    <rect x="0" y="0" width="132" height="132" rx="36" fill="url(#emblem)"/>
    <g transform="translate(6,6)">{mic_emblem(120)}</g>
  </g>
  <text x="278" y="158" font-size="82" font-weight="800" fill="#F8FAFC" letter-spacing="-1">WisperLocal</text>
  <text x="282" y="206" font-size="29" font-weight="600" fill="#93C5FD">Private, on-device dictation for Windows</text>
  <text x="282" y="242" font-size="18.5" fill="#7C8BA5">Press a hotkey &#183; speak &#183; it types where your cursor is &#8212; powered by Whisper</text>
  <g>
      {bars_fg}
  </g>
</svg>
"""


def overlay():
    W, H = 820, 230
    px, py, pw, ph = 178, 64, 464, 92
    cy = py + ph / 2
    bars = wave_bars(30, px + 70, cy, 10, 6, 54, "url(#obars)", envelope=True, phase=0.9)
    bx_cancel, bx_ok = px + pw - 132, px + pw - 60
    r = 24
    return f"""<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">
  <defs>
    <linearGradient id="obars" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7DD3FC"/><stop offset="1" stop-color="#3B82F6"/>
    </linearGradient>
    <linearGradient id="okbtn" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#60A5FA"/><stop offset="1" stop-color="#2563EB"/>
    </linearGradient>
  </defs>
  <ellipse cx="{px + pw/2:.0f}" cy="{py + ph + 22:.0f}" rx="{pw*0.46:.0f}" ry="16" fill="#0F172A" opacity="0.18"/>
  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="{ph/2}" fill="#18181B" fill-opacity="0.97"/>
  <circle cx="{px + 40}" cy="{cy:.0f}" r="8" fill="#EF4444"/>
  {bars}
  <circle cx="{bx_cancel}" cy="{cy:.0f}" r="{r}" fill="#ffffff" fill-opacity="0.14"/>
  <line x1="{bx_cancel-8}" y1="{cy-8:.0f}" x2="{bx_cancel+8}" y2="{cy+8:.0f}" stroke="#FCA5A5" stroke-width="3" stroke-linecap="round"/>
  <line x1="{bx_cancel-8}" y1="{cy+8:.0f}" x2="{bx_cancel+8}" y2="{cy-8:.0f}" stroke="#FCA5A5" stroke-width="3" stroke-linecap="round"/>
  <circle cx="{bx_ok}" cy="{cy:.0f}" r="{r}" fill="url(#okbtn)"/>
  <path d="M{bx_ok-9} {cy:.0f} l6 7 l12 -14" fill="none" stroke="#ffffff" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="{px + pw/2:.0f}" y="{py + ph + 48:.0f}" text-anchor="middle" font-size="19" fill="#64748B">Listening &#8230; press the hotkey again, or click &#10003; to insert</text>
</svg>
"""


(DOCS / "banner.svg").write_text(banner(), encoding="utf-8")
(DOCS / "overlay.svg").write_text(overlay(), encoding="utf-8")
print("wrote", DOCS / "banner.svg")
print("wrote", DOCS / "overlay.svg")
