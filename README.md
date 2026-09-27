# doomzed

[NvChad](https://nvchad.com)'s **doomchad** theme, ported to [Zed](https://zed.dev), plus a matching NvChad-style icon theme.

This repository holds two Zed extensions. Zed's registry requires themes and icon themes to be published separately:

| Directory | Extension ID | Provides |
| --- | --- | --- |
| [`theme/`](theme) | `doomchad-theme` | **Doomchad** (dark) and **Doomchad Light** |
| [`icons/`](icons) | `doomchad-icons` | **Doomchad Icons** and **Doomchad Icons Light** |

## What makes it doomchad

- Colours come straight from base46's `doomchad.lua`, including its quirks: functions are purple, keywords blue, brackets yellow, struct fields blue.
- Syntax follows base46's tree-sitter mapping (`integrations/treesitter.lua`), translated to Zed's highlight captures.
- The UI layering matches NvChad: a darker file tree and pickers, the `black2` tab strip, the `statusline_bg` status bar, and the vim mode indicator coloured like NvChad's statusline blocks.
- Comments are brighter than base46's `grey_fg`, which is hard to read.
- The light variant is not in NvChad. It mirrors the dark surfaces across OKLab lightness, keeping the slate tint. Its accents are darkened to at least 4.2:1 contrast (syntax 4.6:1), and their relative lightness is preserved so each pair stays distinct.
- The icons use the glyphs NvChad shows in nvim-tree. They come from [nvim-web-devicons](https://github.com/nvim-tree/nvim-web-devicons) and Nerd Fonts, recoloured with base46's devicon overrides, and every other brand colour is snapped to the nearest doomchad colour.

## Try it locally

In Zed, run `zed: install dev extension` and pick `theme/`, then do the same for `icons/`. Then select the themes:

```jsonc
"theme": { "mode": "system", "light": "Doomchad Light", "dark": "Doomchad" },
"icon_theme": { "mode": "system", "light": "Doomchad Icons Light", "dark": "Doomchad Icons" }
```

## Regenerating

Everything under `theme/themes` and `icons/icon_themes` + `icons/icons` is generated:

```sh
uv run build/generate.py
```

The script pins its upstream sources: Nerd Fonts v3.5.1 and an nvim-web-devicons commit. It caches them in `build/.cache`. Palette tweaks go in `DARK_30` / `DARK_16`, and the light variant is derived from them.

## Credits

- Palette: [NvChad/base46](https://github.com/NvChad/base46) `doomchad`, itself based on [doom-one](https://github.com/doomemacs/themes) by Henrik Lissner.
- Icons: see [`icons/THIRD_PARTY_NOTICES.md`](icons/THIRD_PARTY_NOTICES.md).

MIT licensed.
