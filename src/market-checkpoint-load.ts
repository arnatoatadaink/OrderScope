import type { CoverageCheckpointPort, StoredCoverageCheckpoint } from "./checkpoint.ts";
import { coverageKeyFor } from "./schedule.ts";
import type { UniverseInstrument, UniverseSnapshot } from "./universe.ts";

function logicalVariant(instrument: UniverseInstrument, feed: string): string {
  return instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : `stock:${feed}:raw`;
}

/**
 * Load the complete Market checkpoint set used by the current scheduler.
 * This intentionally exposes the point-read fan-out for Stage-B capacity tests.
 */
export async function loadMarketCheckpoints(
  universe: UniverseSnapshot,
  checkpoints: CoverageCheckpointPort,
  feed: string,
): Promise<readonly StoredCoverageCheckpoint[]> {
  return (await Promise.all(universe.instruments.map((instrument) => {
    const scope = instrument.providerRoute === "alpaca_crypto_bars" ? "ALL_TRADING" : "REGULAR";
    return checkpoints.get(coverageKeyFor(instrument, scope, logicalVariant(instrument, feed)));
  }))).filter((checkpoint): checkpoint is StoredCoverageCheckpoint => checkpoint !== undefined);
}
