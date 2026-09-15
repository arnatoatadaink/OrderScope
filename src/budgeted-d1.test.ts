import assert from "node:assert/strict";
import test from "node:test";
import { budgetedD1 } from "./budgeted-d1.ts";
import { InvocationBudget } from "./invocation-budget.ts";

test("D1 budget exhaustion fails before issuing an over-ceiling statement", async () => {
  let issued = 0;
  const statement = {
    bind() { return this; },
    async first() { issued += 1; return null; },
  };
  const db = { prepare: () => statement } as unknown as D1Database;
  const budget = new InvocationBudget(40, 1);
  const protectedDb = budgetedD1(db, budget);

  await protectedDb.prepare("SELECT 1").first();
  assert.throws(() => protectedDb.prepare("SELECT 2").first(), /D1_BUDGET/);
  assert.equal(issued, 1);
  assert.equal(budget.snapshot().d1Queries, 1);
});
