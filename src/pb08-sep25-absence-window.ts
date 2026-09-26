import type { AcquisitionJob } from './schedule.ts';
import type { CoverageAbsenceEvidence } from './execution.ts';
import { PB08_SEP25_ABSENCES } from './pb08-sep25-absence-evidence.ts';

// Temporary PB-08 window only. Checked-in deployments omit this gate.
export function pb08Sep25AbsencesForJob(
  job: AcquisitionJob, gate: string | undefined, feed: string, now: Date,
): readonly CoverageAbsenceEvidence[] {
  if (gate === undefined || gate === 'false') return [];
  if (gate !== 'true') throw new Error('invalid PB-08 Sep25 absence gate');
  if (feed !== 'iex') throw new Error('PB-08 evidence requires IEX');
  if (!Number.isFinite(now.getTime()) || now.getTime() > Date.parse('2026-09-26T13:30:00.000Z')) throw new Error('PB-08 Sep25 evidence window expired');
  if (job.interval !== '1Min' || job.providerRoute !== 'alpaca_stock_bars'
    || (job.logicalDataVariant !== undefined && job.logicalDataVariant !== 'stock:iex:raw')
    || job.sessionScope !== 'REGULAR'
    || job.requestedRange.startInclusive < '2026-09-25T13:30:00.000Z'
    || job.requestedRange.endExclusive > '2026-09-25T20:00:00.000Z') return [];
  const symbols = new Set(job.instruments.filter(i => i.cadence === '1Min'
    && i.providerRoute === 'alpaca_stock_bars').map(i => i.symbol));
  return PB08_SEP25_ABSENCES.filter(a => symbols.has(a.symbol)
    && a.identityStart >= job.requestedRange.startInclusive
    && a.identityStart < job.requestedRange.endExclusive);
}
