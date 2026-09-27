#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.20"]
# ///
"""Check the generated extensions the way Zed will load them.

    uv run build/validate.py

Validates each theme file against the Zed schema it names, checks that every
icon path resolves, and that each extension carries its own licence and a
plain major.minor.patch version, as the extension registry requires.
"""

import json
import re
import sys
import tomllib
import urllib.request
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
EXTENSIONS = {
    "theme": ROOT / "theme" / "themes" / "doomed.json",
    "icons": ROOT / "icons" / "icon_themes" / "doomed-icons.json",
}


def schema_errors(doc):
    # zed.dev answers urllib's default User-Agent with 403
    req = urllib.request.Request(doc["$schema"], headers={"User-Agent": "doomed-validate"})
    with urllib.request.urlopen(req) as r:
        schema = json.load(r)
    validator = jsonschema.validators.validator_for(schema)(schema)
    return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in validator.iter_errors(doc)]


def icon_errors(doc, ext_dir):
    errors = []
    for theme in doc["themes"]:
        paths = [*theme["directory_icons"].values(), *theme["chevron_icons"].values(),
                 *(icon["path"] for icon in theme["file_icons"].values())]
        errors += (f"{theme['name']}: missing file {p}" for p in paths if not (ext_dir / p).is_file())
        ids = {*theme["file_stems"].values(), *theme["file_suffixes"].values()}
        errors += (f"{theme['name']}: unknown icon id {i}" for i in sorted(ids - theme["file_icons"].keys()))
    return errors


def manifest_errors(ext_dir):
    errors = []
    manifest = tomllib.loads((ext_dir / "extension.toml").read_text())
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", manifest["version"]):
        errors.append(f"version {manifest['version']!r} is not major.minor.patch")
    if not any(p.name.upper().startswith(("LICENSE", "LICENCE")) for p in ext_dir.iterdir()):
        errors.append("no LICENSE inside the extension directory")
    return errors


def main():
    failed = False
    for name, path in EXTENSIONS.items():
        doc = json.loads(path.read_text())
        errors = schema_errors(doc) + manifest_errors(path.parent.parent)
        if name == "icons":
            errors += icon_errors(doc, path.parent.parent)
        print(f"{name}: {'ok' if not errors else f'{len(errors)} error(s)'}")
        for e in errors[:20]:
            print(f"  {e}")
        failed |= bool(errors)
    sys.exit(failed)


if __name__ == "__main__":
    main()
