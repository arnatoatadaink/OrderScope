import type { CoverageCheckpointPort, StoredCoverageCheckpoint } from "./checkpoint.ts";
import { coverageKeyFor } from "./schedule.ts";
import type { UniverseInstrument, UniverseSnapshot } from "./universe.ts";

function logicalVariant(instrument: UniverseInstrument, feed: string): string {
  return instrument.providerRoute === "alpaca_crypto_bars" ? "crypto:us" : `stock:${feed}:raw`;
}

/**
 * Load the complete Market checkpoint set used by the current scheduler.
 * The complete key set is resolved through one bounded, set-oriented read.
 */
export async function loadMarketCheckpoints(
  universe: UniverseSnapshot,
  checkpoints: CoverageCheckpointPort,
  feed: string,
): Promise<readonly StoredCoverageCheckpoint[]> {
  const coverageKeys = universe.instruments.map((instrument) => {
    const scope = instrument.providerRoute === "alpaca_crypto_bars" ? "ALL_TRADING" : "REGULAR";
    return coverageKeyFor(instrument, scope, logicalVariant(instrument, feed));
  });
  return checkpoints.getMany(coverageKeys);
}
