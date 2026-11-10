"""Colour-contrast audit for Feast Fast (WCAG 2.1).

Run:  python design_audit.py
Reads the real colour tokens from main.py / dashboard.py, so re-run it whenever
you change the palette. Thresholds: 4.5:1 body text, 3:1 large text, icons and
UI boundaries (inputs, focus ring). Exit code is 1 if anything fails.
"""
import sys

from main import C, THEMES
from dashboard import PAGE_BG, SIDEBAR, SIDEBAR_ACTIVE, SIDEBAR_HOVER
from create_account import STRENGTH

WHITE = "#FFFFFF"
TEXT, UI = 4.5, 3.0


def _lum(hex_colour):
    h = hex_colour.lstrip("#")
    chans = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in chans]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(fg, bg):
    hi, lo = sorted((_lum(fg), _lum(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


PAIRS = [
    # (what it is, foreground, background, minimum)
    ("Body text on cream page", C["ink"], C["bg"], TEXT),
    ("Body text on white card", C["ink"], C["card"], TEXT),
    ("Body text on dashboard bg", C["ink"], PAGE_BG, TEXT),
    ("Muted text on cream", C["muted"], C["bg"], TEXT),
    ("Muted text on white", C["muted"], C["card"], TEXT),
    ("Muted text on dashboard bg", C["muted"], PAGE_BG, TEXT),
    ("Muted text on input field", C["muted"], C["field"], TEXT),
    ("Placeholder on input field", C["placeholder"], C["field"], TEXT),
    ("Red link/price on white", C["primary"], C["card"], TEXT),
    ("Red headline on cream", C["primary"], C["bg"], TEXT),
    ("Red badge text on soft red", C["primary"], C["primary_soft"], TEXT),
    ("White text on red button", WHITE, C["primary"], TEXT),
    ("White text on red button (hover)", WHITE, C["primary_hover"], TEXT),
    ("White text on orange button", WHITE, C["accent"], TEXT),
    ("White text on orange button (hover)", WHITE, C["accent_hover"], TEXT),
    ("Orange text on white", C["accent"], C["card"], TEXT),
    ("Error text on white", C["error"], C["card"], TEXT),
    ("Error text on error banner", C["error"], C["error_soft"], TEXT),
    ("Success text on success banner", C["success"], C["success_soft"], TEXT),
    ("Sidebar text", WHITE, SIDEBAR, TEXT),
    ("Sidebar text (hover)", WHITE, SIDEBAR_HOVER, TEXT),
    ("Sidebar text (active)", WHITE, SIDEBAR_ACTIVE, TEXT),
    ("Sidebar logo (graphic)", C["accent_on_dark"], SIDEBAR, UI),
    ("Toast text", WHITE, C["ink"], TEXT),
    ("Input border on white (UI)", C["input_border"], C["card"], UI),
    ("Input border on field (UI)", C["input_border"], C["field"], UI),
    ("Focus ring on white (UI)", C["ink"], C["card"], UI),
    ("Outline button border on white (UI)", C["input_border"], WHITE, UI),
]
for theme, t in THEMES.items():
    PAIRS += [(f"Brand panel '{theme}': heading", WHITE, t["bg"], TEXT),
              (f"Brand panel '{theme}': subtitle", t["sub"], t["bg"], TEXT)]
for label, _bar, ink in STRENGTH[1:]:
    PAIRS.append((f"Password strength '{label}' label", ink, C["card"], TEXT))


def main():
    failures = 0
    print(f"{'':6}{'ratio':>7}{'min':>6}   pair")
    for name, fg, bg, need in PAIRS:
        r = ratio(fg, bg)
        ok = r >= need
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL':6}{r:7.2f}{need:6.1f}   {name}  ({fg} on {bg})")
    print(f"\n{len(PAIRS) - failures}/{len(PAIRS)} combinations pass")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
