#!/usr/bin/env bash
set -euo pipefail

uv run autosort.py -u

# Only continue if autosort.py changed whitelist or blacklist
if git status --porcelain -- whitelist blacklist | grep -q .; then
    git add whitelist blacklist
    git commit -m "updated lists by autosort"
    git push
    sudo pihole updateGravity
fi
