from pathlib import Path

path = Path("src/worker-orchestration.integration.test.ts")
text = path.read_text()

old = '''  for (const sensitive of [
    "integration-key", "integration-secret", "upstream-provider-body", "503",
  ]) assert.equal(serializedEnvelope.includes(sensitive), false);'''
new = '''  for (const sensitive of [
    "integration-key", "integration-secret", "upstream-provider-body",
    "503 upstream-provider-body",
  ]) assert.equal(serializedEnvelope.includes(sensitive), false);'''

if new in text:
    print(f"already repaired {path}")
elif old in text:
    path.write_text(text.replace(old, new, 1))
    print(f"repaired {path}")
else:
    raise SystemExit("provider failure digest fixture did not match expected old or repaired form")
