"""Save/check real API output across an actual application/database restart.

Usage:
    python tests/replay_snapshot.py save tests/.runtime/restart.json
    # Restart API and PostgreSQL without changing lookup data or generator version.
    python tests/replay_snapshot.py check tests/.runtime/restart.json
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request


CASES = [
    {"locale": "en_US", "seed": "restart-replay", "batch": 0, "batch_size": 10},
    {"locale": "de_DE", "seed": "restart-replay", "batch": 1234, "batch_size": 17},
    {"locale": "en_US", "seed": "O'Reilly & Grüße", "batch": 33_333, "batch_size": 30},
]


def capture():
    base = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
    result = []
    for params in CASES:
        url = base + "/api/users?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=60) as response:
            assert response.status == 200
            result.append({"request": params, "response": json.loads(response.read())})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("save", "check"))
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    if args.mode == "save":
        data = capture()
        # Exclusive creation prevents accidentally replacing the pre-restart evidence.
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        with args.snapshot.open("x", encoding="utf-8") as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
        print(f"Saved {len(CASES)} API cases to {args.snapshot}")
    else:
        expected = json.loads(args.snapshot.read_text(encoding="utf-8"))
        actual = capture()
        for saved, current in zip(expected, actual, strict=True):
            assert current == saved, f"Restart changed generated output: {saved['request']}"
        count = sum(len(case["response"]["users"]) for case in actual)
        print(f"Restart replay passed: {len(CASES)} cases, {count} records identical")


if __name__ == "__main__":
    main()
