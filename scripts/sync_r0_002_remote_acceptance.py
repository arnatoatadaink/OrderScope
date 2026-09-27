from pathlib import Path

p = Path('docs/work-management/local-corporate-intelligence/LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER_2026-09-05.md')
text = p.read_text(encoding='utf-8')
text = text.replace(
    '| R0-002 | Accepted locally | Packet D durable run evidence/restart recovery accepted |',
    '| R0-002 | Accepted — remote schema gate closed | Packet D accepted; migration `0008_scheduler_run_evidence.sql` applied to live-canary D1 and post-apply verified; scheduler evidence activation remains separately gated |'
)
text = text.replace(
    '| R0-002 | locally Accepted through Packet D |',
    '| R0-002 | Accepted; `0008` remote schema applied and verified; scheduler-evidence activation still gated |'
)
text = text.replace(
    '- Packet D is locally Accepted. Remote migration `0008`, scheduler-evidence activation, Worker deployment/Cron mutation, and any live confirmation remain separately gated.',
    '- Packet D is Accepted and remote migration `0008` is applied/verified on live-canary. Scheduler-evidence activation, Worker deployment/Cron mutation, and any live confirmation remain separately gated.'
)
p.write_text(text, encoding='utf-8')
print(p)
