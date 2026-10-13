#!/usr/bin/env python3
"""Build skills/dist/dc-maintenance-notices.skill (zip with the skill folder at its root)."""
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = "dc-maintenance-notices"
OUT = os.path.join(HERE, "dist", f"{SKILL}.skill")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(os.path.join(HERE, SKILL)):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".pyc"):
                path = os.path.join(root, f)
                z.write(path, os.path.relpath(path, HERE))
print(f"built {OUT}")
