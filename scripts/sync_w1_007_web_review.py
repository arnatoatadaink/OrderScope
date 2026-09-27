from pathlib import Path

TRACKER = Path("docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md")
text = TRACKER.read_text()

old = """Next CP gate: Web review of the W1-007 evidence, then a separately authorized\nshort monitored W1-001 confirmation/closeout window. The cadence predicate is\nalready repaired and live-confirmed; it is no longer the active blocker.\n"""
new = """W1-007 Web review is Accepted as of 2026-09-13. The read-only diagnostic evidence,\nsafe rollback baseline, and current Wrangler/D1 command semantics were reviewed\nwithout remote mutation. The next CP gate is a separately authorized short monitored\nW1-001 confirmation/closeout window. See `W1-007_WEB_REVIEW_2026-09-13.md` and\n`W1-001_CONFIRMATION_CLOSEOUT_CHANGE_WINDOW_2026-09-13.md`.\n"""
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("expected W1-007 gate paragraph not found")

old = """- `W1-001` reopen collected 12 successful eligible News opportunities and then safely rolled back after Cloudflare API authorization/control loss; W1-007 has restored the read-only control-path gate locally, pending Web review before another live window.\n"""
new = """- `W1-001` reopen collected 12 successful eligible News opportunities and then safely rolled back after Cloudflare API authorization/control loss; W1-007 local diagnostic and Web review are Accepted. A short confirmation/closeout window is Ready but remains separately authorization-gated.\n"""
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("expected parallel-lane W1-001 paragraph not found")

old = """3. Treat W1-007 as locally Accepted through two successful read-only passes; obtain Web review before any separately authorized short W1-001 confirmation/closeout window. Root cause of the earlier `7403` remains unknown.\n"""
new = """3. Treat W1-007 local diagnostic and Web review as Accepted. The next gate is a separately authorized short W1-001 confirmation/closeout window. Root cause of the earlier `7403` remains unknown.\n"""
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("expected restart-rule W1-007 paragraph not found")

old = """| W1-007 | locally Accepted; two read-only passes of whoami, D1 info, SELECT 1, and PRAGMA succeeded; no 7403/quota error; earlier 7403 root cause remains unknown; rollback version remains shadow with News disabled |\n"""
new = """| W1-007 | local diagnostic + Web review Accepted; two read-only passes of whoami, D1 info, SELECT 1, and PRAGMA succeeded; no 7403/quota error; safe Shadow/News-disabled baseline retained; short W1-001 closeout window Ready but separately authorization-gated |\n"""
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("expected latest-evidence W1-007 row not found")

TRACKER.write_text(text)
print(f"updated {TRACKER}")
