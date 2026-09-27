# Doomed

**Your NvChad setup, in Zed.** Doomed ports NvChad's *doomchad*, its take on Doom One, to Zed, together with the nvim-tree file icons that go with it. You get the same colours, the same file tree and the same statusline blocks, so moving from Neovim doesn't mean giving up the look you tuned for years.

![Doomed and Doomed Light side by side](assets/hero.png)

## Install

1. In Zed, open the extensions page (<kbd>cmd</kbd>-<kbd>shift</kbd>-<kbd>x</kbd>).
2. Search for **Doomed** and install both **Doomed** (the theme) and **Doomed Icons**.
3. Pick them with `theme selector: toggle` and `icon theme selector: toggle`, or follow the system appearance:

```jsonc
// ~/.config/zed/settings.json
"theme": { "mode": "system", "light": "Doomed Light", "dark": "Doomed" },
"icon_theme": { "mode": "system", "light": "Doomed Icons Light", "dark": "Doomed Icons" }
```

## Why Doomed

**It's doomchad, not another Doom One.** Colours come straight from NvChad's [base46](https://github.com/NvChad/base46) `doomchad.lua`, including the quirks that make it recognisable: purple functions, blue keywords, yellow brackets, blue struct fields. Syntax follows base46's tree-sitter mapping, translated to Zed's highlight captures.

**The whole window, not just the editor.** It keeps NvChad's layering: a darker file tree and pickers, the tab strip one step lighter, and a separate statusline. Zed's vim mode badge takes NvChad's statusline colours: blue for normal, purple for insert, green for visual, orange for replace.

**Comments you can read.** base46's comment grey is famously hard to read on the doomchad background. Doomed brightens it, and doc comments one step further.

**A light variant NvChad never had.** Doomed Light mirrors the dark surfaces across OKLab lightness, so it keeps doomchad's slate tint instead of turning into plain white. Every accent is darkened to at least 4.2:1 contrast (4.6:1 for syntax), and the accents keep their relative lightness, so colours that differ in the dark theme still differ in the light one.

**Icons that match your nvim-tree.** Doomed Icons uses the Nerd Font glyphs from [nvim-web-devicons](https://github.com/nvim-tree/nvim-web-devicons), the ones NvChad shows, for about 500 extensions and 540 file names. The folder and default-file glyphs match NvChad's nvim-tree config. Colours use base46's devicon overrides where they exist, and every other brand colour is snapped to the nearest doomchad colour, so the file tree fits the theme instead of looking like confetti.

<picture>
  <source media="(prefers-color-scheme: light)" srcset="assets/icons-light.svg">
  <img alt="A sample of Doomed Icons: Rust, TypeScript, Go, Python, Lua, Nushell, Docker, Nix and more" src="assets/icons-dark.svg">
</picture>

## Screenshots

<details open>
<summary><b>Doomed</b></summary>

![Doomed](assets/dark.png)

</details>

<details>
<summary><b>Doomed Light</b></summary>

![Doomed Light](assets/light.png)

</details>

The project in the screenshots is [`assets/demo`](assets/demo), a small repository that exists to show off syntax and icons.

## What's in this repository

Zed's registry publishes themes and icon themes as separate extensions, so this repository holds two:

| Directory | Extension | Provides |
| --- | --- | --- |
| [`theme/`](theme) | `doomed-theme` | **Doomed** and **Doomed Light** |
| [`icons/`](icons) | `doomed-icons` | **Doomed Icons** and **Doomed Icons Light** |

Everything in them is generated. To tweak the palette, edit `DARK_30` / `DARK_16` in [`build/generate.py`](build/generate.py). The light variant is derived from them. Then run:

```sh
uv run build/generate.py   # themes, icon theme, SVGs, notices
uv run build/validate.py   # Zed schemas, icon paths, licences, versions
uv run build/showcase.py   # README images, after new screenshots
```

The script pins its upstream sources, Nerd Fonts v3.5.1 and an nvim-web-devicons commit, and caches them in `build/.cache`. CI regenerates everything on each push and fails if the committed files differ or don't validate.

To try local changes, run `zed: install dev extension` in Zed and pick `theme/`, then `icons/`.

## Credits

- Palette: [NvChad/base46](https://github.com/NvChad/base46) `doomchad`, itself based on [doom-one](https://github.com/doomemacs/themes) by Henrik Lissner.
- Icons: [nvim-web-devicons](https://github.com/nvim-tree/nvim-web-devicons) and [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts). Per-glyph licences are in [`icons/THIRD_PARTY_NOTICES.md`](icons/THIRD_PARTY_NOTICES.md).

MIT licensed.
