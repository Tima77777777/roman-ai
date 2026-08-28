"""Machine-readable check against policy.json (P1) — formalizes the "no autonomous
irreversible actions" rule from docs/ARCHITECTURE.md, раздел 1.3.

Usage as a library:
    from policy_check import requires_owner_approval
    if requires_owner_approval("change_repository_visibility"):
        # stop, report to owner instead of doing it
        ...

Usage as CLI (for quick manual checks): python policy_check.py <action_category>
"""
import json
import sys
from pathlib import Path

POLICY_FILE = Path(__file__).resolve().parent.parent / "policy.json"


def _load() -> dict:
    return json.loads(POLICY_FILE.read_text(encoding="utf-8-sig"))


def requires_owner_approval(action_category: str) -> bool:
    """True = the executor must NOT perform this autonomously — flag it to the owner instead.
    Defaults to True (requires approval) for any category not explicitly whitelisted —
    matches the "default to caution" note in policy.json."""
    policy = _load()
    if action_category in policy.get("always_allowed", []):
        return False
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python policy_check.py <action_category>", file=sys.stderr)
        sys.exit(1)
    category = sys.argv[1]
    needs_approval = requires_owner_approval(category)
    print("REQUIRES_OWNER_APPROVAL" if needs_approval else "ALLOWED")
    sys.exit(1 if needs_approval else 0)
