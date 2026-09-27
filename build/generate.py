#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools>=4.50"]
# ///
"""Generate the Doomchad Zed theme and icon theme.

    uv run build/generate.py

Writes theme/themes/doomchad.json, icons/icon_themes/doomchad-icons.json and
icons/icons/{dark,light}/*.svg. Upstream sources are downloaded into
build/.cache on first run and pinned below.
"""

import colorsys
import json
import math
import re
import shutil
import tarfile
import urllib.request
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "build" / ".cache"

THEME_FAMILY = "Doomchad"
THEME_DARK = "Doomchad"
THEME_LIGHT = "Doomchad Light"
ICONS_FAMILY = "Doomchad Icons"
ICONS_DARK = "Doomchad Icons"
ICONS_LIGHT = "Doomchad Icons Light"
AUTHOR = "Mate Alfoldi"

NERD_FONTS = "https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/NerdFontsSymbolsOnly.tar.xz"
DEVICONS = "https://raw.githubusercontent.com/nvim-tree/nvim-web-devicons/58447c1fca354bbf184425e4a8d01deecbd6f3c4/lua/nvim-web-devicons/default"


# ── colour maths (OKLab / OKLCH, WCAG contrast) ────────────────────────────────

def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def rgb_hex(rgb):
    return "#" + "".join(f"{round(min(max(c, 0), 1) * 255):02x}" for c in rgb)


def oklch(h):
    r, g, b = (_lin(c) for c in hex_rgb(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def _oklch_rgb(L, C, H):
    A, B = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
    m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
    s = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
    return [_gam(v) for v in (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )]


def from_oklch(L, C, H):
    # shrink chroma until the colour fits in sRGB
    while C > 0:
        rgb = _oklch_rgb(L, C, H)
        if all(-1e-4 <= v <= 1 + 1e-4 for v in rgb):
            return rgb_hex(rgb)
        C -= 0.002
    return rgb_hex(_oklch_rgb(L, 0, H))


def luminance(h):
    r, g, b = (_lin(c) for c in hex_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def darken_to(h, bg, target):
    """Keep hue and chroma, lower OKLab lightness until `h` reaches `target` contrast on `bg`."""
    L, C, H = oklch(h)
    out = h
    while contrast(out, bg) < target and L > 0.05:
        L -= 0.005
        out = from_oklch(L, C, H)
    return out


def a(h, alpha):
    return f"{h}{round(alpha * 255):02x}"


def mix(fg, bg, pct_fg):
    return rgb_hex([x * pct_fg + y * (1 - pct_fg) for x, y in zip(hex_rgb(fg), hex_rgb(bg))])


# ── palettes ───────────────────────────────────────────────────────────────────

# NvChad base46 doomchad (base_30 + base_16), comments brightened.
DARK_30 = dict(
    white="#bbc2cf", darker_black="#22262e", black="#282c34", black2="#2e323a",
    one_bg="#32363e", one_bg2="#3c4048", one_bg3="#41454d", grey="#494d55",
    grey_fg="#53575f", grey_fg2="#5d6169", light_grey="#676b73", red="#ff6b5a",
    baby_pink="#ff7665", pink="#ff75a0", line="#3b3f47", green="#98be65",
    vibrant_green="#a9cf76", nord_blue="#47a5e5", blue="#51afef", yellow="#ecbe7b",
    sun="#f2c481", purple="#dc8ef3", dark_purple="#c678dd", teal="#4db5bd",
    orange="#ea9558", cyan="#46d9ff", statusline_bg="#2d3139", lightbg="#3a3e46",
    comment="#838893", comment_doc="#959aa5",
)
DARK_16 = dict(
    base00="#282c34", base01="#32363e", base02="#3c4048", base03="#4e525a",
    base04="#5a5e66", base05="#a7aebb", base06="#b3bac7", base07="#bbc2cf",
    base08="#ff6c6b", base09="#ea9558", base0A="#ecbe7b", base0B="#98be65",
    base0C="#66c4ff", base0D="#dc8ef3", base0E="#48a6e6", base0F="#c85a50",
)

NEUTRALS_30 = ["darker_black", "black", "black2", "one_bg", "one_bg2", "one_bg3", "grey",
               "grey_fg", "grey_fg2", "light_grey", "line", "statusline_bg", "lightbg"]
ACCENTS_30 = ["red", "baby_pink", "pink", "green", "vibrant_green", "nord_blue", "blue",
              "yellow", "sun", "purple", "dark_purple", "teal", "orange", "cyan"]
ACCENTS_16 = ["base08", "base09", "base0A", "base0B", "base0C", "base0D", "base0E", "base0F"]


def mirror(h, pivot=1.2, offset=0.0):
    """Reflect a dark-theme surface across OKLab lightness, keeping a softened slate tint."""
    L, C, H = oklch(h)
    return from_oklch(pivot - L - offset, C * 0.75, H)


def mirror_accent(h, bg, target):
    """Brighter-in-dark accents become darker-in-light, so pairs stay distinct."""
    L, C, H = oklch(h)
    return darken_to(from_oklch(0.52 - 0.5 * (L - 0.72), C, H), bg, target)


FG_GREYS = ("grey", "grey_fg", "grey_fg2", "light_grey")


def make_light():
    c, b = {}, {}
    for k in NEUTRALS_30:
        c[k] = mirror(DARK_30[k], offset=0.08 if k in FG_GREYS else 0.0)
    for k in ("base00", "base01", "base03", "base04"):
        b[k] = mirror(DARK_16[k], offset=0.08 if k in ("base03", "base04") else 0.0)
    bg = c["black"]
    # text: darker than a plain mirror would give, so it reads crisply on grey
    _, C, H = oklch(DARK_30["white"])
    c["white"] = b["base07"] = from_oklch(0.24, C, H)
    b["base06"] = from_oklch(0.28, C, H)
    b["base05"] = from_oklch(0.32, C, H)
    b["base02"] = from_oklch(oklch(bg)[0] - 0.08, 0.04, 255)  # visual selection, faint blue
    c["comment"] = darken_to(DARK_30["comment"], bg, 3.6)
    c["comment_doc"] = darken_to(DARK_30["comment_doc"], bg, 4.4)
    for k in ACCENTS_30:
        c[k] = mirror_accent(DARK_30[k], bg, 4.2)
    for k in ACCENTS_16:
        b[k] = mirror_accent(DARK_16[k], bg, 4.6)
    # base0C and base0E are both sky blue in doomchad; on a light ground they
    # collapse into one colour, so constructors/escapes take doom's cyan
    b["base0C"] = mirror_accent(DARK_30["cyan"], bg, 4.6)
    return c, b


LIGHT_30, LIGHT_16 = make_light()

DARK_TERM = dict(black="one_bg", bright_black="grey_fg2", dim_black="black2",
                 white="base05", bright_white="white", dim_white="light_grey")
LIGHT_TERM = dict(black="base05", bright_black="light_grey", dim_black="base06",
                  white="grey", bright_white="black2", dim_white="grey_fg")


# ── theme ──────────────────────────────────────────────────────────────────────

def s(color, style=None, weight=None):
    return {"color": color, "font_style": style, "font_weight": weight}


def build_theme(c, b, t):
    pick = lambda k: c.get(t[k]) or b[t[k]]

    style = {
        "background.appearance": "opaque",
        "accents": [c["blue"], c["dark_purple"], c["green"], c["yellow"], c["orange"], c["teal"], c["pink"]],

        # chrome
        "background": c["darker_black"],
        "border": c["line"],
        "border.variant": c["one_bg"],
        "border.focused": a(c["blue"], .55),
        "border.selected": a(c["blue"], .35),
        "border.transparent": "#00000000",
        "border.disabled": c["one_bg"],
        "surface.background": c["darker_black"],
        "elevated_surface.background": c["darker_black"],
        "panel.background": c["darker_black"],
        "panel.focused_border": None,
        "panel.indent_guide": mix(c["line"], c["darker_black"], .8),
        "panel.indent_guide_active": c["grey"],
        "panel.indent_guide_hover": c["grey_fg"],
        "panel.overlay_background": c["darker_black"],
        "panel.overlay_hover": c["black2"],
        "pane.focused_border": None,
        "pane_group.border": c["line"],
        "title_bar.background": c["darker_black"],
        "title_bar.inactive_background": c["darker_black"],
        "status_bar.background": c["statusline_bg"],
        "toolbar.background": c["black"],
        "tab_bar.background": c["black2"],
        "tab.inactive_background": c["black2"],
        "tab.active_background": c["black"],
        "drop_target.background": a(c["blue"], .12),
        "drop_target.border": c["blue"],

        # elements
        "element.background": c["one_bg"],
        "element.hover": c["one_bg2"],
        "element.active": c["one_bg3"],
        "element.selected": c["one_bg2"],
        "element.disabled": c["one_bg"],
        "element.selection_background": a(c["blue"], .3),
        "ghost_element.background": "#00000000",
        "ghost_element.hover": c["black2"],
        "ghost_element.active": c["one_bg2"],
        "ghost_element.selected": c["one_bg"],
        "ghost_element.disabled": "#00000000",

        # text & icons
        "text": c["white"],
        "text.muted": mix(c["white"], c["light_grey"], .5),
        "text.placeholder": c["light_grey"],
        "text.disabled": c["grey_fg2"],
        "text.accent": c["blue"],
        "icon": b["base05"],
        "icon.muted": c["light_grey"],
        "icon.disabled": c["grey_fg"],
        "icon.placeholder": c["light_grey"],
        "icon.accent": c["blue"],
        "link_text.hover": c["blue"],
        "debugger.accent": c["red"],

        # scrollbars / minimap
        "scrollbar.thumb.background": a(c["grey"], .6),
        "scrollbar.thumb.hover_background": c["grey"],
        "scrollbar.thumb.active_background": c["grey_fg"],
        "scrollbar.thumb.border": "#00000000",
        "scrollbar.track.background": "#00000000",
        "scrollbar.track.border": "#00000000",
        "minimap.thumb.background": a(c["grey"], .35),
        "minimap.thumb.hover_background": a(c["grey"], .55),
        "minimap.thumb.active_background": a(c["grey"], .75),
        "minimap.thumb.border": "#00000000",

        # editor
        "editor.foreground": b["base05"],
        "editor.background": c["black"],
        "editor.gutter.background": c["black"],
        "editor.subheader.background": c["black2"],
        "editor.active_line.background": c["black2"],
        "editor.highlighted_line.background": c["black2"],
        "editor.debugger_active_line.background": a(c["yellow"], .12),
        "editor.line_number": c["grey"],
        "editor.active_line_number": c["white"],
        "editor.hover_line_number": c["light_grey"],
        "editor.invisible": b["base03"],
        "editor.wrap_guide": a(c["line"], .6),
        "editor.active_wrap_guide": c["line"],
        "editor.indent_guide": c["line"],
        "editor.indent_guide_active": c["grey"],
        "editor.code_lens.foreground": c["light_grey"],
        "editor.document_highlight.read_background": a(c["grey"], .55),
        "editor.document_highlight.write_background": a(c["grey"], .8),
        "editor.document_highlight.bracket_background": c["grey"],
        "search.match_background": a(c["yellow"], .25),
        "search.active_match_background": a(c["orange"], .45),

        # git / diff
        "version_control.added": c["green"],
        "version_control.modified": c["yellow"],
        "version_control.deleted": c["red"],
        "version_control.renamed": c["blue"],
        "version_control.conflict": c["orange"],
        "version_control.ignored": c["light_grey"],
        "version_control.word_added": a(c["green"], .25),
        "version_control.word_deleted": a(c["red"], .25),
        "version_control.conflict_marker.ours": a(c["green"], .1),
        "version_control.conflict_marker.theirs": a(c["blue"], .1),
        "editor.diff_hunk.added.background": mix(c["green"], c["black"], .1),
        "editor.diff_hunk.added.hollow_background": mix(c["green"], c["black"], .05),
        "editor.diff_hunk.added.hollow_border": mix(c["green"], c["black"], .35),
        "editor.diff_hunk.deleted.background": mix(c["red"], c["black"], .1),
        "editor.diff_hunk.deleted.hollow_background": mix(c["red"], c["black"], .05),
        "editor.diff_hunk.deleted.hollow_border": mix(c["red"], c["black"], .35),

        # vim modes: NvChad statusline blocks, visual on green so it doesn't
        # blur into normal's blue
        "vim.normal.background": c["nord_blue"],   "vim.normal.foreground": c["black"],
        "vim.insert.background": c["dark_purple"], "vim.insert.foreground": c["black"],
        "vim.visual.background": c["green"],       "vim.visual.foreground": c["black"],
        "vim.visual_line.background": c["green"],  "vim.visual_line.foreground": c["black"],
        "vim.visual_block.background": c["green"], "vim.visual_block.foreground": c["black"],
        "vim.replace.background": c["orange"],     "vim.replace.foreground": c["black"],
        "vim.helix_normal.background": c["nord_blue"], "vim.helix_normal.foreground": c["black"],
        "vim.helix_select.background": c["green"], "vim.helix_select.foreground": c["black"],
        "vim.helix_jump_label.foreground": c["red"],
        "vim.yank.background": a(c["orange"], .3),

        # terminal
        "terminal.background": c["black"],
        "terminal.foreground": b["base05"],
        "terminal.bright_foreground": c["white"],
        "terminal.dim_foreground": c["light_grey"],
        "terminal.ansi.background": c["black"],
        "terminal.ansi.black": pick("black"), "terminal.ansi.bright_black": pick("bright_black"), "terminal.ansi.dim_black": pick("dim_black"),
        "terminal.ansi.white": pick("white"), "terminal.ansi.bright_white": pick("bright_white"), "terminal.ansi.dim_white": pick("dim_white"),
    }
    for ansi, (normal, bright) in {
        "red": ("red", "baby_pink"), "green": ("green", "vibrant_green"), "yellow": ("yellow", "sun"),
        "blue": ("blue", "nord_blue"), "magenta": ("dark_purple", "purple"), "cyan": ("teal", "cyan"),
    }.items():
        style[f"terminal.ansi.{ansi}"] = c[normal]
        style[f"terminal.ansi.bright_{ansi}"] = c[bright]
        style[f"terminal.ansi.dim_{ansi}"] = mix(c[normal], c["black"], .7)

    # diagnostics & status (NvChad: error red, warn yellow, hint purple)
    for name, col in [("error", c["red"]), ("warning", c["yellow"]), ("info", c["blue"]),
                      ("hint", c["purple"]), ("success", c["green"]), ("created", c["green"]),
                      ("modified", c["yellow"]), ("deleted", c["red"]), ("conflict", c["orange"]),
                      ("renamed", c["blue"]), ("predictive", c["grey_fg2"]),
                      ("ignored", c["light_grey"]), ("hidden", c["light_grey"]),
                      ("unreachable", c["grey_fg2"])]:
        style[name] = col
        style[name + ".background"] = mix(col, c["black"], .12)
        style[name + ".border"] = mix(col, c["black"], .35)

    players = [c["blue"], c["dark_purple"], c["green"], c["orange"], c["teal"], c["yellow"], c["pink"], c["red"]]
    style["players"] = [{"cursor": p, "background": p, "selection": a(p, .25)} for p in players]
    style["players"][0]["selection"] = b["base02"]  # Visual = base02

    # syntax: base46 treesitter.lua + doomchad polish_hl
    style["syntax"] = {
        "attribute":               s(b["base0A"]),
        "attribute.jsx":           s(b["base08"]),         # @tag.attribute
        "boolean":                 s(b["base09"]),
        "comment":                 s(c["comment"]),
        "comment.doc":             s(c["comment_doc"]),
        "constant":                s(b["base09"]),
        "constant.builtin":        s(b["base09"]),
        "constructor":             s(b["base0C"]),
        "embedded":                s(b["base05"]),
        "emphasis":                s(b["base09"], "italic"),
        "emphasis.strong":         s(b["base09"], weight=700),
        "enum":                    s(b["base0A"]),
        "function":                s(b["base0D"]),
        "function.builtin":        s(b["base0D"]),
        "function.decorator":      s(b["base0A"]),
        "function.special":        s(b["base08"]),         # macros → @function.macro
        "hint":                    s(c["light_grey"]),
        "keyword":                 s(b["base0E"]),
        "keyword.import":          s(b["base0D"]),         # @keyword.import → Include
        "keyword.directive":       s(b["base0A"]),
        "label":                   s(b["base0A"]),
        "lifetime":                s(b["base0A"]),
        "link_text":               s(b["base0C"]),
        "link_uri":                s(b["base09"]),
        "namespace":               s(b["base08"]),         # @module
        "number":                  s(b["base09"]),
        "operator":                s(b["base05"]),
        "predictive":              s(c["grey_fg2"], "italic"),
        "preproc":                 s(b["base0A"]),
        "primary":                 s(b["base05"]),
        "property":                s(c["blue"]),           # doomchad @variable.member
        "property.json_key":       s(b["base08"]),         # @property
        "punctuation":             s(b["base0F"]),
        "punctuation.bracket":     s(c["yellow"]),         # doomchad polish
        "punctuation.delimiter":   s(b["base0F"]),
        "punctuation.list_marker": s(b["base08"]),
        "punctuation.markup":      s(b["base0F"]),
        "punctuation.special":     s(b["base0C"]),
        "selector":                s(b["base0A"]),
        "selector.pseudo":         s(b["base0E"]),
        "string":                  s(b["base0B"]),
        "string.escape":           s(b["base0C"]),
        "string.regex":            s(b["base0C"]),
        "string.special":          s(b["base0C"]),
        "string.special.symbol":   s(b["base0B"]),
        "tag":                     s(b["base0A"]),
        "text.literal":            s(b["base09"]),
        "title":                   s(b["base0D"], weight=700),
        "type":                    s(b["base0A"]),
        "type.builtin":            s(b["base0A"]),
        "variable":                s(b["base05"]),
        "variable.parameter":      s(b["base08"]),
        "variable.special":        s(b["base09"]),         # self/this → @variable.builtin
        "variant":                 s(b["base09"]),
        "diff.plus":               s(c["green"]),
        "diff.minus":              s(c["red"]),
    }
    return style


# ── icons ──────────────────────────────────────────────────────────────────────

# NvChad nvim-tree glyphs (nvchad/configs/nvimtree.lua) and codicon chevrons
GLYPH_FILE = 0xF021A
GLYPH_FOLDER = 0xE6AD
GLYPH_FOLDER_OPEN = 0xEAF6
GLYPH_CHEVRON_RIGHT = 0xEAB6
GLYPH_CHEVRON_DOWN = 0xEAB4

# base46 integrations/devicons.lua: DevIcon<name> overrides, matched case-insensitively
BASE46_DEVICONS = {
    "c": "blue", "css": "blue", "deb": "cyan", "dockerfile": "cyan", "html": "baby_pink",
    "jpeg": "dark_purple", "jpg": "dark_purple", "js": "sun", "kt": "orange", "lock": "red",
    "lua": "blue", "mp3": "white", "mp4": "white", "out": "white", "png": "dark_purple",
    "py": "cyan", "toml": "blue", "ts": "teal", "ttf": "white", "rb": "pink", "rpm": "orange",
    "vue": "vibrant_green", "woff": "white", "woff2": "white", "xz": "sun", "zip": "sun",
    "zig": "orange", "md": "blue", "tsx": "blue", "jsx": "blue", "svelte": "red",
    "java": "orange", "dart": "cyan",
}

# Nerd Fonts v3 glyph sets, for the notices file
GLYPH_SETS = [
    ((0xE5FA, 0xE6B7), "Seti-UI + Custom", "MIT", "https://github.com/jesseweed/seti-ui"),
    ((0xE700, 0xE8EF), "Devicons", "MIT", "https://github.com/vorillaz/devicons"),
    ((0xE200, 0xE2A9), "Font Awesome Extension", "MIT", "https://github.com/AndreLZGava/font-awesome-extension"),
    ((0xE300, 0xE3E3), "Weather Icons", "SIL OFL 1.1", "https://github.com/erikflowers/weather-icons"),
    ((0xEA60, 0xEC1E), "Codicons", "CC BY 4.0", "https://github.com/microsoft/vscode-codicons"),
    ((0xED00, 0xF2FF), "Font Awesome", "CC BY 4.0", "https://github.com/FortAwesome/Font-Awesome"),
    ((0xF300, 0xF381), "Font Logos", "Unlicense", "https://github.com/lukas-w/font-logos"),
    ((0xF400, 0xF533), "Octicons", "MIT", "https://github.com/primer/octicons"),
    ((0xF0001, 0xF1AF0), "Material Design Icons", "Apache 2.0", "https://github.com/Templarian/MaterialDesign"),
]


def fetch(url, dest):
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print("fetch", url)
        with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
    return dest


def load_font():
    font_path = CACHE / "SymbolsNerdFont-Regular.ttf"
    if not font_path.exists():
        with tarfile.open(fetch(NERD_FONTS, CACHE / "NerdFontsSymbolsOnly.tar.xz")) as tar:
            tar.extract("SymbolsNerdFont-Regular.ttf", CACHE, filter="data")
    font = TTFont(font_path)
    return font.getGlyphSet(), font.getBestCmap()


def load_devicons(table):
    src = fetch(f"{DEVICONS}/{table}.lua", CACHE / f"{table}.lua").read_text()
    pat = re.compile(r'\["(.+?)"\]\s*=\s*\{\s*icon\s*=\s*"(.+?)",\s*color\s*=\s*"(#\w{6})".*?name\s*=\s*"(.+?)"')
    return [m.groups() for m in map(pat.search, src.splitlines()) if m]


def nearest_role(hex_):
    """Snap a devicons brand colour to the closest doomchad base_30 colour."""
    L, C, H = oklch(hex_)
    if C < 0.04:
        return "white" if L > 0.7 else "light_grey"

    def dist(role):
        L2, C2, H2 = oklch(DARK_30[role])
        dh = min(abs(H - H2), 360 - abs(H - H2)) / 180
        return (dh * 2.5) ** 2 + (L - L2) ** 2 + (C - C2) ** 2

    return min(ACCENTS_30, key=dist)


def glyph_svg(glyphs, cmap, cp, color, box=14.0):
    g = glyphs[cmap[cp]]
    bp = BoundsPen(glyphs)
    g.draw(bp)
    x0, y0, x1, y1 = bp.bounds
    sc = box / max(x1 - x0, y1 - y0)
    tx, ty = 8 - (x0 + x1) / 2 * sc, 8 + (y0 + y1) / 2 * sc
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    g.draw(TransformPen(pen, (sc, 0, 0, -sc, tx, ty)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
            f'<path fill="{color}" d="{pen.getCommands()}"/></svg>\n')


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def build_icons():
    glyphs, cmap = load_font()
    by_ext = load_devicons("icons_by_file_extension")
    by_name = load_devicons("icons_by_filename")

    icons = {}      # (codepoint, role) -> icon id
    suffixes, stems = {}, {}
    used = set()

    def icon_for(glyph, color, name, key=""):
        cp = ord(glyph)
        if cp not in cmap:
            return None
        role = BASE46_DEVICONS.get(key.lower()) or BASE46_DEVICONS.get(name.lower()) or nearest_role(color)
        key = (cp, role)
        if key not in icons:
            base, n = slug(name) or f"u{cp:x}", 2
            ident = base
            while ident in icons.values():
                ident, n = f"{base}_{n}", n + 1
            icons[key] = ident
        used.add(cp)
        return icons[key]

    for ext, glyph, color, name in by_ext:
        if (ident := icon_for(glyph, color, name, ext)):
            suffixes[ext] = ident
    for fname, glyph, color, name in by_name:
        if (ident := icon_for(glyph, color, name)):
            stems[fname] = ident
            # devicons matches filenames case-insensitively; Zed does not,
            # so add the spellings people actually use (Makefile, LICENSE, README.md)
            stem, dot, rest = fname.partition(".")
            for variant in (fname[:1].upper() + fname[1:], stem.upper() + dot + rest):
                stems.setdefault(variant, ident)

    specials = {
        "default": (GLYPH_FILE, "white"),
        "folder": (GLYPH_FOLDER, "folder"),
        "folder_open": (GLYPH_FOLDER_OPEN, "folder"),
        "chevron_right": (GLYPH_CHEVRON_RIGHT, "light_grey"),
        "chevron_down": (GLYPH_CHEVRON_DOWN, "folder"),
    }
    used.update(cp for cp, _ in specials.values())

    out_dir = ROOT / "icons" / "icons"
    shutil.rmtree(out_dir, ignore_errors=True)
    themes = []
    for variant, pal, name in (("dark", DARK_30, ICONS_DARK), ("light", LIGHT_30, ICONS_LIGHT)):
        vdir = out_dir / variant
        vdir.mkdir(parents=True)
        tones = pal | {
            "folder": pal["blue"],
            # neutral icons: full-strength text is too heavy for a light file tree
            "white": pal["white"] if variant == "dark" else mix(pal["white"], pal["light_grey"], .45),
        }
        colour = tones.__getitem__
        for (cp, role), ident in icons.items():
            (vdir / f"{ident}.svg").write_text(glyph_svg(glyphs, cmap, cp, colour(role)))
        for ident, (cp, role) in specials.items():
            box = 11.0 if ident.startswith("chevron") else 14.0
            (vdir / f"_{ident}.svg").write_text(glyph_svg(glyphs, cmap, cp, colour(role), box))
        p = lambda ident: f"./icons/{variant}/{ident}.svg"
        themes.append({
            "name": name,
            "appearance": variant,
            "directory_icons": {"collapsed": p("_folder"), "expanded": p("_folder_open")},
            "chevron_icons": {"collapsed": p("_chevron_right"), "expanded": p("_chevron_down")},
            "file_stems": dict(sorted(stems.items())),
            "file_suffixes": dict(sorted(suffixes.items())),
            "file_icons": {"default": {"path": p("_default")}}
                          | {ident: {"path": p(ident)} for ident in sorted(icons.values())},
        })

    write_json(ROOT / "icons" / "icon_themes" / "doomchad-icons.json", {
        "$schema": "https://zed.dev/schema/icon_themes/v0.3.0.json",
        "name": ICONS_FAMILY,
        "author": AUTHOR,
        "themes": themes,
    })
    write_notices(used)
    print(f"icons: {len(icons)} glyph/colour pairs, {len(suffixes)} suffixes, {len(stems)} file names")


def write_notices(used):
    rows = []
    for (lo, hi), project, lic, url in GLYPH_SETS:
        n = sum(lo <= cp <= hi for cp in used)
        if n:
            rows.append(f"| [{project}]({url}) | {lic} | {n} |")
    (ROOT / "icons" / "THIRD_PARTY_NOTICES.md").write_text(f"""# Third-party notices

The SVG icons in `icons/` are glyph outlines extracted from
[Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) v3.5.1 (Symbols Nerd Font),
recoloured with the doomchad palette. Each glyph keeps the licence of the project
it comes from:

| Glyph source | Licence | Glyphs used |
| --- | --- | --- |
{chr(10).join(rows)}

The file-name and extension to icon mapping is derived from
[nvim-web-devicons](https://github.com/nvim-tree/nvim-web-devicons)
(MIT, Copyright (c) 2020 Kyazdani42), and the folder and default-file glyphs and
colour overrides follow [NvChad](https://github.com/NvChad/NvChad)'s nvim-tree
and base46 devicons configuration.
""")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main():
    write_json(ROOT / "theme" / "themes" / "doomchad.json", {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": THEME_FAMILY,
        "author": AUTHOR,
        "themes": [
            {"name": THEME_DARK, "appearance": "dark", "style": build_theme(DARK_30, DARK_16, DARK_TERM)},
            {"name": THEME_LIGHT, "appearance": "light", "style": build_theme(LIGHT_30, LIGHT_16, LIGHT_TERM)},
        ],
    })
    print("theme: written")
    build_icons()


if __name__ == "__main__":
    main()
