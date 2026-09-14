#!/usr/bin/env python3
"""Build the profile hero SVGs: extract used glyphs, subset fonts, embed as data URIs.

Inputs:  src/hero-dark.svg, src/hero-light.svg  (templates with {{SG700}}/{{SG500}}/{{JB500}})
Fonts:   /tmp/SpaceGrotesk.ttf, /tmp/JetBrainsMono.ttf  (variable, OFL)
Outputs: assets/hero-dark.svg, assets/hero-light.svg
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

SG = "/tmp/SpaceGrotesk.ttf"
JB = "/tmp/JetBrainsMono.ttf"

TEMPLATES = ["hero-dark.svg", "hero-light.svg"]


def used_chars() -> str:
    chars = set()
    for name in TEMPLATES:
        text = (SRC / name).read_text()
        for m in re.finditer(r"<text[^>]*>(.*?)</text>", text, re.S):
            chars.update(html.unescape(m.group(1)))
    return "".join(sorted(chars))


def subset_font(variable_ttf: str, weight: int, text: str, out_path: Path) -> bytes:
    inst = TTFont(variable_ttf)
    static = instantiateVariableFont(inst, {"wght": weight}, inplace=True)
    tmp = WORK / f"{out_path.stem}-{weight}.ttf"
    static.save(tmp)

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.layout_features = ["kern", "liga", "calt"]
    opts.notdef_outline = True
    font = subset.load_font(str(tmp), opts)
    ss = subset.Subsetter(options=opts)
    ss.populate(text=text)
    ss.subset(font)
    subset.save_font(font, str(out_path), opts)
    return out_path.read_bytes()


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def main() -> None:
    text = used_chars()
    print(f"glyph set ({len(text)} chars): {text!r}")

    sg700 = b64(subset_font(SG, 700, text, WORK / "sg700.woff2"))
    sg500 = b64(subset_font(SG, 500, text, WORK / "sg500.woff2"))
    jb500 = b64(subset_font(JB, 500, text, WORK / "jb500.woff2"))
    print(f"sizes: sg700={len(sg700)//1024}KB sg500={len(sg500)//1024}KB jb500={len(jb500)//1024}KB (base64)")

    for name in TEMPLATES:
        svg = (SRC / name).read_text()
        svg = svg.replace("{{SG700}}", sg700).replace("{{SG500}}", sg500).replace("{{JB500}}", jb500)
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
