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
