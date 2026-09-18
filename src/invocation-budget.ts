export const EXTERNAL_SUBREQUEST_CEILING = 40;
export const D1_QUERY_CEILING = 40;

export type BudgetKind = "external" | "d1";

export class InvocationBudget {
  private external = 0;
  private d1 = 0;
  readonly externalCeiling: number;
  readonly d1Ceiling: number;

  constructor(externalCeiling = EXTERNAL_SUBREQUEST_CEILING, d1Ceiling = D1_QUERY_CEILING) {
    this.externalCeiling = externalCeiling;
    this.d1Ceiling = d1Ceiling;
  }

  consume(kind: BudgetKind, count = 1): void {
    if (!Number.isSafeInteger(count) || count < 0) throw new Error("budget count must be a non-negative integer");
    const used = kind === "external" ? this.external : this.d1;
    const ceiling = kind === "external" ? this.externalCeiling : this.d1Ceiling;
    if (used + count > ceiling) throw new Error(kind === "external" ? "EXTERNAL_BUDGET" : "D1_BUDGET");
    if (kind === "external") this.external += count;
    else this.d1 += count;
  }

  remaining(kind: BudgetKind): number {
    return (kind === "external" ? this.externalCeiling - this.external : this.d1Ceiling - this.d1);
  }

  snapshot() { return { externalSubrequests: this.external, d1Queries: this.d1 }; }
}
