export type SessionKind = "PREMARKET" | "REGULAR" | "AFTER_HOURS";

export type NormalizedMarketSession = {
  marketDate: string;
  sessionKind: SessionKind;
  opensAt: string;
  closesAt: string;
  isShortened: boolean;
  calendarRevision: string;
};

export type MarketCalendarSnapshot = {
  market: string;
  dateRange: { startInclusive: string; endExclusive: string };
  sessions: readonly NormalizedMarketSession[];
  generatedAt: string;
  revision: string;
};

export interface MarketCalendarProvider {
  getCalendar(startDate: string, endDate: string): Promise<MarketCalendarSnapshot>;
}

export type AlpacaCalendarCredentials = {
  keyId: string;
  secretKey: string;
};

export type AlpacaCalendarProviderOptions = {
  credentials: AlpacaCalendarCredentials;
  baseUrl?: string;
  fetcher?: typeof fetch;
  now?: () => Date;
  includePremarket?: boolean;
};

type AlpacaCalendarDay = {
  date: string;
  open: string;
  close: string;
};

const MARKET_TIMEZONE = "America/New_York";
const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const TIME_PATTERN = /^(\d{2}):(\d{2})$/;
const REGULAR_SESSION_MINUTES = 390;
const PREMARKET_OPEN = "04:00";

function assertDate(value: string, name: string): void {
  const parsed = new Date(`${value}T00:00:00Z`);
  if (!DATE_PATTERN.test(value) || Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    throw new Error(`${name} must be a valid YYYY-MM-DD date`);
  }
}

function previousDate(date: string): string {
  const value = new Date(`${date}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() - 1);
  return value.toISOString().slice(0, 10);
}

function timezoneOffsetMilliseconds(instant: Date, timeZone: string): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).formatToParts(instant);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const representedAsUtc = Date.UTC(
    Number(values.year),
    Number(values.month) - 1,
    Number(values.day),
    Number(values.hour),
    Number(values.minute),
    Number(values.second),
  );
  return representedAsUtc - instant.getTime();
}

function marketLocalInstant(date: string, time: string): string {
  const match = TIME_PATTERN.exec(time);
  if (!match) throw new Error(`invalid Alpaca calendar time: ${time}`);
  const [year, month, day] = date.split("-").map(Number);
  const wallClockAsUtc = Date.UTC(year, month - 1, day, Number(match[1]), Number(match[2]));
  let result = new Date(wallClockAsUtc);

  // Resolve the IANA-zone offset at the target date. A second pass handles an
  // initial guess falling on the other side of a DST boundary.
  for (let pass = 0; pass < 2; pass += 1) {
    result = new Date(wallClockAsUtc - timezoneOffsetMilliseconds(result, MARKET_TIMEZONE));
  }
  return result.toISOString();
}

function isCalendarDay(value: unknown): value is AlpacaCalendarDay {
  if (typeof value !== "object" || value === null) return false;
  return "date" in value
    && typeof value.date === "string"
    && DATE_PATTERN.test(value.date)
    && "open" in value
    && typeof value.open === "string"
    && TIME_PATTERN.test(value.open)
    && "close" in value
    && typeof value.close === "string"
    && TIME_PATTERN.test(value.close);
}

function revisionFor(sessions: readonly NormalizedMarketSession[]): string {
  const canonical = sessions.map((session) =>
    `${session.marketDate}|${session.sessionKind}|${session.opensAt}|${session.closesAt}|${session.isShortened}`,
  ).join(";");
  let hash = 0x811c9dc5;
  for (let index = 0; index < canonical.length; index += 1) {
    hash ^= canonical.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return `alpaca-calendar-v2:${(hash >>> 0).toString(16).padStart(8, "0")}`;
}

export class AlpacaMarketCalendarProvider implements MarketCalendarProvider {
  private readonly credentials: AlpacaCalendarCredentials;
  private readonly baseUrl: string;
  private readonly fetcher: typeof fetch;
  private readonly now: () => Date;
  private readonly includePremarket: boolean;

  constructor(options: AlpacaCalendarProviderOptions) {
    this.credentials = options.credentials;
    this.baseUrl = options.baseUrl ?? "https://paper-api.alpaca.markets";
    const fetcher = options.fetcher ?? fetch;
    // Workerd's global fetch is receiver-sensitive. Calling a stored reference
    // as `this.fetcher(...)` otherwise supplies the provider as its receiver and
    // fails at runtime with "Illegal invocation".
    this.fetcher = (input, init) => fetcher(input, init);
    this.now = options.now ?? (() => new Date());
    this.includePremarket = options.includePremarket ?? false;
  }

  async getCalendar(startDate: string, endDate: string): Promise<MarketCalendarSnapshot> {
    assertDate(startDate, "startDate");
    assertDate(endDate, "endDate");
    if (startDate >= endDate) throw new Error("calendar range must be non-empty and half-open");

    const url = new URL("/v2/calendar", this.baseUrl);
    url.searchParams.set("start", startDate);
    // Alpaca's date range is inclusive; Core calendar ranges are half-open.
    url.searchParams.set("end", previousDate(endDate));
    const response = await this.fetcher(url, {
      headers: {
        "APCA-API-KEY-ID": this.credentials.keyId,
        "APCA-API-SECRET-KEY": this.credentials.secretKey,
      },
    });
    if (!response.ok) throw new Error(`alpaca market calendar failed: ${response.status}`);

    const payload: unknown = await response.json();
    if (!Array.isArray(payload) || !payload.every(isCalendarDay)) {
      throw new Error("alpaca market calendar response has an invalid schema");
    }

    const provisional = payload.flatMap((day): NormalizedMarketSession[] => {
      if (day.date < startDate || day.date >= endDate) {
        throw new Error(`alpaca market calendar returned out-of-range date: ${day.date}`);
      }
      const opensAt = marketLocalInstant(day.date, day.open);
      const closesAt = marketLocalInstant(day.date, day.close);
      const durationMinutes = (Date.parse(closesAt) - Date.parse(opensAt)) / 60_000;
      if (durationMinutes <= 0) throw new Error(`invalid Alpaca session duration: ${day.date}`);
      const regular: NormalizedMarketSession = {
        marketDate: day.date,
        sessionKind: "REGULAR",
        opensAt,
        closesAt,
        isShortened: durationMinutes < REGULAR_SESSION_MINUTES,
        calendarRevision: "pending",
      };
      if (!this.includePremarket) return [regular];
      const premarketOpensAt = marketLocalInstant(day.date, PREMARKET_OPEN);
      if (Date.parse(premarketOpensAt) >= Date.parse(opensAt)) {
        throw new Error(`invalid Alpaca Premarket duration: ${day.date}`);
      }
      return [{
        marketDate: day.date,
        sessionKind: "PREMARKET",
        opensAt: premarketOpensAt,
        closesAt: opensAt,
        isShortened: false,
        calendarRevision: "pending",
      }, regular];
    });
    provisional.sort((left, right) => left.opensAt.localeCompare(right.opensAt)
      || left.sessionKind.localeCompare(right.sessionKind));
    const revision = revisionFor(provisional);
    const sessions = provisional.map((session) => ({ ...session, calendarRevision: revision }));

    return {
      market: "US_EQUITIES",
      dateRange: { startInclusive: startDate, endExclusive: endDate },
      sessions,
      generatedAt: this.now().toISOString(),
      revision,
    };
  }
}

export function sessionAt(
  snapshot: MarketCalendarSnapshot,
  instantUtc: Date,
): NormalizedMarketSession | undefined {
  const ms = instantUtc.getTime();
  return snapshot.sessions.find((session) => {
    const open = Date.parse(session.opensAt);
    const close = Date.parse(session.closesAt);
    return ms >= open && ms < close;
  });
}

// No weekday/DST fallback exists by design. If the authoritative calendar is
// unavailable, the scheduler must report UNKNOWN/BLOCKED rather than invent a session.
