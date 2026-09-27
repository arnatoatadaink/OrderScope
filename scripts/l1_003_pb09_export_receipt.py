"""Verify two bounded read results against accepted Phase A custody; no writes."""
import hashlib
import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: l1_003_pb09_export_receipt.py <read1.json> <read2.json>")
def require(condition, message):
    if not condition:
        raise SystemExit(message)

root = Path(__file__).resolve().parent.parent
custody = root / "var/d1-custody/l1-003-smoke-007-20260915"
expected = (custody / "normalized_bar_20260901T160300Z_20260901T160400Z.ndjson").read_bytes()
manifest = json.loads((custody / "export-manifest.json").read_text())
require(len(expected) == 581 and hashlib.sha256(expected).hexdigest() == manifest["sha256"] == "de380ae35c1ab50f5e0364585e7f3224512085dc3bcd4abff8e37631938bed56", "accepted custody bytes changed")
for path in sys.argv[1:]:
    groups = json.loads(Path(path).read_text())
    require(isinstance(groups, list) and len(groups) == 1 and groups[0]["success"] is True, "invalid read envelope")
    require(groups[0]["meta"]["changed_db"] is False, "read mutated D1")
    rows = groups[0]["results"]
    require(len(rows) == 1, "source row count changed")
    row = rows[0]
    require("2026-09-01T16:03:00.000Z" <= row["bar_start_utc"] < "2026-09-01T16:04:00.000Z", "source row escaped frozen window")
    actual = (json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    require(actual == expected, "source differs from accepted custody; stop without replacing custody")
print(json.dumps({"repeatIdentity": "PASS", "inheritedCustody": "PASS", "rowCount": 1, "bytes": len(expected), "sha256": manifest["sha256"], "remoteMutation": False}))
