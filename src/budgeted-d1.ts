import type { InvocationBudget } from "./invocation-budget";

const EXECUTION_METHODS = new Set(["all", "first", "raw", "run"]);

/** Charge immediately before each actual D1 statement is issued. */
export function budgetedD1(db: D1Database, budget: InvocationBudget): D1Database {
  const wrapStatement = (statement: D1PreparedStatement): D1PreparedStatement => new Proxy(statement, {
    get(target, property, receiver) {
      if (property === "bind") return (...values: unknown[]) => wrapStatement(target.bind(...values));
      if (typeof property === "string" && EXECUTION_METHODS.has(property)) {
        return (...args: unknown[]) => {
          budget.consume("d1");
          return (Reflect.get(target, property, target) as (...inner: unknown[]) => unknown).apply(target, args);
        };
      }
      const value: unknown = Reflect.get(target, property, receiver);
      return typeof value === "function" ? value.bind(target) : value;
    },
  });

  return new Proxy(db, {
    get(target, property, receiver) {
      if (property === "prepare") return (query: string) => wrapStatement(target.prepare(query));
      if (property === "batch") {
        return <T = unknown>(statements: D1PreparedStatement[]) => {
          budget.consume("d1", statements.length);
          return target.batch<T>(statements);
        };
      }
      const value: unknown = Reflect.get(target, property, receiver);
      return typeof value === "function" ? value.bind(target) : value;
    },
  });
}
