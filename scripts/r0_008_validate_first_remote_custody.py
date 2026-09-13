from __future__ import annotations

import json
from pathlib import Path

from orderscope_local.market_import.d1_manifest import decode_d1_export_manifest
from orderscope_local.storage.d1_custody import decode_d1_custody_manifest
from orderscope_local.storage.d1_custody_quality import validate_d1_custody_artifact

ROOT = Path("var/d1-custody/r0-007-first-remote")
ARTIFACT = ROOT / "normalized_bar_20260901T160300Z_20260901T160400Z.ndjson"
EXPORT_MANIFEST = ROOT / "export-manifest.json"
CUSTODY_MANIFEST = ROOT / "custody-manifest.json"
EXPECTED_GENERATION_ID = "d1-custody-5b7c680a337a817950b2de12fa5ee18be54ef06b3336e7386872ded4d87494c7"

artifact = ARTIFACT.read_bytes()
export = decode_d1_export_manifest(json.loads(EXPORT_MANIFEST.read_text(encoding="utf-8")))
custody = decode_d1_custody_manifest(json.loads(CUSTODY_MANIFEST.read_text(encoding="utf-8")))
quality = validate_d1_custody_artifact(manifest=export, artifact=artifact)

if custody.export.manifest_id != export.manifest_id:
    raise SystemExit("custody/export manifest identity mismatch")
if custody.generation_id != EXPECTED_GENERATION_ID:
    raise SystemExit("unexpected custody generation identity")
if not quality.quality_accepted:
    raise SystemExit("quality was not accepted")
if quality.row_count != 1:
    raise SystemExit("unexpected row count")

print(f"quality_accepted = {quality.quality_accepted}")
print(f"row_count        = {quality.row_count}")
print(f"artifact_sha256  = {quality.artifact_sha256}")
print(f"manifest_id      = {quality.manifest_id}")
print(f"generation_id    = {custody.generation_id}")
print("R0-008 first custody quality evidence = PASS")
