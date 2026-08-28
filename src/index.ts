export interface Env {
  WORKER_MODE?: "shadow" | "live";
  MARKET_TIMEZONE?: string;
  DISPLAY_TIMEZONE?: string;
  ALPACA_FEED?: "iex" | "sip" | "delayed_sip";
  ALPACA_API_KEY_ID?: string;
  ALPACA_API_SECRET_KEY?: string;
  STATE_DB?: D1Database;
  BAR_ARCHIVE?: R2Bucket;
}

type Digest = {
  generatedAt: string;
  mode: string;
  status: "shadow" | "ready" | "blocked";
  marketTimezone: string;
  feed: string;
  notes: string[];
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function currentDigest(env: Env, now: Date): Digest {
  const hasCredentials = Boolean(env.ALPACA_API_KEY_ID && env.ALPACA_API_SECRET_KEY);
  const hasState = Boolean(env.STATE_DB);
  const hasArchive = Boolean(env.BAR_ARCHIVE);
  const liveRequested = env.WORKER_MODE === "live";

  return {
    generatedAt: now.toISOString(),
    mode: env.WORKER_MODE ?? "shadow",
    status: liveRequested && hasCredentials && hasState ? "ready" : liveRequested ? "blocked" : "shadow",
    marketTimezone: env.MARKET_TIMEZONE ?? "America/New_York",
    feed: env.ALPACA_FEED ?? "iex",
    notes: [
      hasCredentials ? "alpaca credentials configured" : "alpaca credentials not configured",
      hasState ? "D1 state binding configured" : "D1 state binding not configured",
      hasArchive ? "R2 archive binding configured" : "R2 archive binding not configured",
      "calendar-aware acquisition is intentionally not simulated from weekday/UTC rules",
    ],
  };
}

async function runScheduledTick(controller: ScheduledController, env: Env): Promise<void> {
  const now = new Date(controller.scheduledTime);
  const digest = currentDigest(env, now);

  // Shadow mode is deployable before credentials/storage exist and deliberately
  // performs no market-data writes. This prevents a calendar/session guess from
  // becoming production behavior.
  if (env.WORKER_MODE !== "live") {
    console.log(JSON.stringify({ event: "scheduler_tick", ...digest }));
    return;
  }

  if (!env.ALPACA_API_KEY_ID || !env.ALPACA_API_SECRET_KEY) {
    throw new Error("live mode requires Alpaca secrets");
  }
  if (!env.STATE_DB) {
    throw new Error("live mode requires STATE_DB D1 binding");
  }

  // Next implementation slice:
  // 1. load versioned Universe (Tier A/B/C),
  // 2. obtain authoritative market calendar/session snapshot,
  // 3. plan due AcquisitionJobs from cadence + checkpoints,
  // 4. call Alpaca historical bars with overlap and pagination,
  // 5. normalize/idempotently accept bars,
  // 6. update D1 checkpoints and compact digest,
  // 7. batch immutable OHLCV archive objects to R2 when configured.
  console.log(JSON.stringify({ event: "scheduler_tick_live_boundary", ...digest }));
}

export default {
  async scheduled(controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(runScheduledTick(controller, env));
  },

  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return json({ ok: true, ...currentDigest(env, new Date()) });
    }

    if (url.pathname === "/digest/latest") {
      // v0.1 returns only sanitized operational state until D1 digest persistence
      // is wired. No secrets/provider credentials are ever included.
      return json(currentDigest(env, new Date()));
    }

    return json({ error: "not_found" }, 404);
  },
} satisfies ExportedHandler<Env>;
