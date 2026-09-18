#!/usr/bin/env python3
"""Build the profile hero SVGs: extract used glyphs, subset fonts, embed as data URIs.

Style: Nous (Hermes desktop theme) — GitHub neutrals + Nous blue.
Fonts:  Inter (sans) + Courier Prime (mono), both OFL, embedded as subsets.
Inputs:  src/hero-landscape-dark.svg, src/hero-landscape-light.svg
Outputs: assets/hero-landscape-dark.svg, assets/hero-landscape-light.svg
"""
import base64
import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools import subset

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
ASSETS = ROOT / "assets"
WORK = ROOT / ".build"
WORK.mkdir(exist_ok=True)

TEMPLATES = ["hero-landscape-v2-dark.svg", "hero-landscape-v2-light.svg"]

# token -> (source ttf, instance axes or None for a static font)
FONTS = {
    "SANS700": ("/tmp/Inter.ttf", {"wght": 700, "opsz": 32}),
    "SANS500": ("/tmp/Inter.ttf", {"wght": 500, "opsz": 20}),
    "MONO700": ("/tmp/CourierPrime-Bold.ttf", None),
}


def used_chars() -> str:
    chars = set()
    for name in TEMPLATES:
        text = (SRC / name).read_text()
        for m in re.finditer(r"<text[^>]*>(.*?)</text>", text, re.S):
            chars.update(html.unescape(m.group(1)))
    return "".join(sorted(chars))


def build_font(token: str, text: str) -> str:
    """Instance (if variable), subset to `text`, return base64 woff2."""
    src, axes = FONTS[token]
    font = TTFont(src)

    missing = sorted({c for c in text if ord(c) not in font.getBestCmap()})
    if missing:
        raise SystemExit(f"{token}: font lacks glyphs {missing!r} — pick another face or change the copy")

    work_file = WORK / f"{token.lower()}.ttf"
    if axes and "fvar" in font:
        instantiateVariableFont(font, axes, inplace=True)
    font.save(work_file)

    out = WORK / f"{token.lower()}.woff2"
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.layout_features = ["kern", "liga", "calt"]
    opts.notdef_outline = True
    sub = subset.load_font(str(work_file), opts)
    ss = subset.Subsetter(options=opts)
    ss.populate(text=text)
    ss.subset(sub)
    subset.save_font(sub, str(out), opts)
    return base64.b64encode(out.read_bytes()).decode()


def main() -> None:
    text = used_chars()
    print(f"glyph set ({len(text)} chars): {text!r}")

    payload = {token: build_font(token, text) for token in FONTS}
    for token, data in payload.items():
        print(f"  {token}: {len(data) // 1024} KB (base64)")

    for name in TEMPLATES:
        svg = (SRC / name).read_text()
        for token, data in payload.items():
            svg = svg.replace(f"{{{{{token}}}}}", data)
        if "{{" in svg:
            raise SystemExit(f"{name}: unreplaced token remains")
        out = ASSETS / name
        out.write_text(svg)
        # SVG must be well-formed XML or browsers/GitHub silently fail to render it
        try:
            ET.parse(out)
        except ET.ParseError as exc:
            out.unlink(missing_ok=True)
            raise SystemExit(f"INVALID XML in {out}: {exc}")
        print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
