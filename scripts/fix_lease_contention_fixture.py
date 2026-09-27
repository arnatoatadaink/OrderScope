from __future__ import annotations

from pathlib import Path

TARGET = Path("src/worker-orchestration.integration.test.ts")


def replace_once(text: str, old: str, new: str, *, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise RuntimeError(f"{label}: neither original nor repaired form was found")


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")

    # Accept either the original sleep-based fixture or the previously attempted
    # cross-request Promise barrier and normalize both to a request-safe boolean gate.
    text = replace_once(
        text,
        '    let providerCalls = 0;\n    let releaseProvider;\n    const providerGate = new Promise((resolve) => { releaseProvider = resolve; });',
        '    let providerCalls = 0;\n    let providerReleased = false;',
        label="provider gate declaration",
    ) if 'let releaseProvider;' in text else replace_once(
        text,
        '    let providerCalls = 0;\n    const calendar = {',
        '    let providerCalls = 0;\n    let providerReleased = false;\n    const calendar = {',
        label="provider gate declaration",
    )

    if 'await providerGate;' in text:
        text = replace_once(
            text,
            '        providerCalls += 1;\n        await providerGate;',
            '        providerCalls += 1;\n        while (!providerReleased) {\n          await new Promise((resolve) => setTimeout(resolve, 10));\n        }',
            label="provider gate wait",
        )
    else:
        text = replace_once(
            text,
            '        providerCalls += 1;\n        await new Promise((resolve) => setTimeout(resolve, 500));',
            '        providerCalls += 1;\n        while (!providerReleased) {\n          await new Promise((resolve) => setTimeout(resolve, 10));\n        }',
            label="provider gate wait",
        )

    if 'releaseProvider?.();' in text:
        text = replace_once(
            text,
            '        if (path === "/control/release-provider") {\n          releaseProvider?.();\n          return new Response("released");\n        }',
            '        if (path === "/control/release-provider") {\n          providerReleased = true;\n          return new Response("released");\n        }',
            label="release endpoint",
        )
    elif 'path === "/control/release-provider"' not in text:
        text = replace_once(
            text,
            '        if (path === "/control/provider-calls") return new Response(String(providerCalls));\n        return worker.fetch(request, env, ctx);',
            '        if (path === "/control/provider-calls") return new Response(String(providerCalls));\n        if (path === "/control/release-provider") {\n          providerReleased = true;\n          return new Response("released");\n        }\n        return worker.fetch(request, env, ctx);',
            label="release endpoint",
        )

    release_assertion = '''  assert.equal(\n    await (await mf.dispatchFetch("http://integration.test/control/release-provider")).text(),\n    "released",\n  );\n\n'''
    if release_assertion not in text:
        text = replace_once(
            text,
            '''  assert.deepEqual(await db.prepare(`SELECT\n    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,\n    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts\n  `).first(), { attempts: 1, receipts: 0 });\n\n  assert.equal((await firstTick).outcome, "ok");''',
            '''  assert.deepEqual(await db.prepare(`SELECT\n    (SELECT COUNT(*) FROM acquisition_attempt) AS attempts,\n    (SELECT COUNT(*) FROM bar_acceptance_receipt) AS receipts\n  `).first(), { attempts: 1, receipts: 0 });\n\n''' + release_assertion + '''  assert.equal((await firstTick).outcome, "ok");''',
            label="provider release assertion",
        )

    TARGET.write_text(text, encoding="utf-8")
    print(f"repaired {TARGET}")


if __name__ == "__main__":
    main()
