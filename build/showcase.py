#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=10"]
# ///
"""Build the README images from the generated themes and the screenshots.

    uv run build/showcase.py

Reads assets/{dark,light}.png (Zed screenshots of assets/demo, same window
size) and the generated icon theme. Writes assets/hero.png, the code half
of both windows side by side, and assets/icons-{dark,light}.svg, an icon wall.
"""

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

FILES = """
main.rs Cargo.toml App.tsx index.ts package.json vite.config.ts
main.go go.mod main.py pyproject.toml notebook.ipynb main.jl
init.lua config.nu build.sh Makefile CMakeLists.txt Justfile
main.c main.cpp Main.java Main.kt main.swift main.zig
main.dart app.rb Gemfile index.php main.ex Main.hs
index.html styles.css main.scss App.vue App.svelte page.astro
Dockerfile flake.nix main.tf config.yaml data.json schema.sql
README.md LICENSE .gitignore .env .editorconfig yarn.lock
logo.png logo.svg song.mp3 clip.mp4 archive.zip font.ttf
""".split()

COLS, CELL_W, CELL_H, PAD = 6, 176, 44, 24


HERO_WIDTH, HERO_GAP, RADIUS = 0.48, 40, 22   # crop: the code half of the window


def hero():
    shots = [Image.open(ASSETS / f"{n}.png").convert("RGBA") for n in ("dark", "light")]
    w, h = shots[0].size
    cw = round(w * HERO_WIDTH)
    out = Image.new("RGBA", (2 * cw + HERO_GAP, h), (0, 0, 0, 0))
    for i, shot in enumerate(shots):
        crop = shot.crop((0, 0, cw, h))
        mask = Image.new("L", crop.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, h - 1), RADIUS, fill=255)
        out.paste(crop, (i * (cw + HERO_GAP), 0), mask)
    out.save(ASSETS / "hero.png", optimize=True)


def resolve(theme, name):
    if name in theme["file_stems"]:
        return theme["file_stems"][name]
    for i, ch in enumerate(name):
        if ch == "." and name[i + 1:] in theme["file_suffixes"]:
            return theme["file_suffixes"][name[i + 1:]]
    return "default"


def icon_wall(theme, style, out):
    rows = -(-len(FILES) // COLS)
    w, h = COLS * CELL_W + 2 * PAD, rows * CELL_H + 2 * PAD
    bg, fg, border = style["panel.background"], style["text"], style["border"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="10" fill="{bg}" stroke="{border}"/>',
        f'<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14" fill="{fg}">',
    ]
    for i, name in enumerate(FILES):
        x, y = PAD + i % COLS * CELL_W, PAD + i // COLS * CELL_H
        svg = (ROOT / "icons" / theme["file_icons"][resolve(theme, name)]["path"]).read_text()
        fill, d = re.search(r'fill="([^"]+)" d="([^"]+)"', svg).groups()
        parts.append(f'<path transform="translate({x} {y + 12}) scale(1.25)" fill="{fill}" d="{d}"/>')
        parts.append(f'<text x="{x + 30}" y="{y + 27}">{name}</text>')
    parts += ["</g>", "</svg>"]
    out.write_text("\n".join(parts) + "\n")


def main():
    hero()
    icons = json.loads((ROOT / "icons" / "icon_themes" / "doomed-icons.json").read_text())["themes"]
    styles = json.loads((ROOT / "theme" / "themes" / "doomed.json").read_text())["themes"]
    for icon_theme, theme in zip(icons, styles):
        icon_wall(icon_theme, theme["style"], ASSETS / f"icons-{icon_theme['appearance']}.svg")
    print("showcase: hero.png, icons-dark.svg, icons-light.svg")


if __name__ == "__main__":
    main()
