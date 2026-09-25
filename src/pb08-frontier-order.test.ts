import assert from "node:assert/strict";
import test from "node:test";
import type { MarketCalendarSnapshot } from "./calendar.ts";
import type { StoredCoverageCheckpoint } from "./checkpoint.ts";
import { prioritizeAcquisitionJobs } from "./job-priority.ts";
import { SchedulePolicy } from "./schedule.ts";
import { loadUniverseSnapshot } from "./universe.ts";

const now0 = "2026-09-25T02:44:38.000Z";
const floor = "2026-09-24T02:44:38.000Z";
const calendar: MarketCalendarSnapshot = {
  market: "US_EQUITIES",
  dateRange: { startInclusive: "2026-09-23", endExclusive: "2026-09-25" },
  generatedAt: now0,
  revision: "pb08-competition-snapshot",
  sessions: [
    { marketDate:"2026-09-23",sessionKind:"REGULAR",opensAt:"2026-09-23T13:30:00.000Z",closesAt:"2026-09-23T20:00:00.000Z",isShortened:false,calendarRevision:"pb08-competition-snapshot" },
    { marketDate:"2026-09-24",sessionKind:"REGULAR",opensAt:"2026-09-24T13:30:00.000Z",closesAt:"2026-09-24T20:00:00.000Z",isShortened:false,calendarRevision:"pb08-competition-snapshot" },
  ],
};

function cp(symbol:string, scope:"REGULAR"|"ALL_TRADING", variant:string, through:string, version:number, state:"COMPLETE"|"PARTIAL"="COMPLETE"): StoredCoverageCheckpoint {
  return {
    coverageKey:`${symbol}|1Min|${scope}|${variant}`, symbol, interval:"1Min", sessionScope:scope,
    logicalDataVariant:variant, completeThrough:through, sourceObservedThrough:through,
    state, missingRanges:[], version, universeRevision:"stock-monitoring-canary-v0.1",
  };
}

test("PB-08 fresh frozen competition reaches the retained NVDA frontier within a bounded number of unchanged Cron opportunities", () => {
  const universe=loadUniverseSnapshot("canary-v0.1");
  const checkpoints:StoredCoverageCheckpoint[]=[
    cp("AMD","REGULAR","stock:iex:raw","2026-09-02T13:51:00.000Z",40,"PARTIAL"),
    cp("QQQ","REGULAR","stock:iex:raw","2026-09-02T15:57:00.000Z",9,"PARTIAL"),
    cp("SPY","REGULAR","stock:iex:raw","2026-09-02T16:49:00.000Z",43),
    cp("NVDA","REGULAR","stock:iex:raw","2026-09-23T18:28:00.000Z",61),
    cp("BTCUSD","ALL_TRADING","crypto:us","2026-09-23T17:58:00.000Z",48),
  ];
  const p=new SchedulePolicy({
    retentionFloor:floor,
    overlapMs:{"1Min":60_000,"15Min":900_000,"1Day":86_400_000},
    finalizationLagMs:{"1Min":60_000,"15Min":120_000,"1Day":1_800_000},
    maxBarsPerJob:100,
    logicalDataVariant:i=>i.providerRoute==="alpaca_crypto_bars"?"crypto:us":"stock:iex:raw",
  });

  const selections:string[][]=[];
  let nvdaJobs=0;
  for(let i=0;i<16;i++){
    // This test freezes the read-only PB-08 snapshot.  Do not advance "now"
    // here: moving-frontier behavior is validated operationally by taking a
    // fresh read-only snapshot immediately after the bounded catch-up window.
    const now=new Date(now0);
    const jobs=prioritizeAcquisitionJobs(p.plan(universe,calendar,checkpoints,now),checkpoints).slice(0,2);
    selections.push(jobs.map(j=>j.instruments[0]!.symbol));
    for(const job of jobs){
      const key=job.checkpointExpectations[0]!.coverageKey;
      const item=checkpoints.find(c=>c.coverageKey===key)!;
      item.completeThrough=job.requestedRange.endExclusive;
      item.sourceObservedThrough=job.requestedRange.endExclusive;
      item.version+=1;
      item.state="COMPLETE";
      if(item.symbol==="NVDA") nvdaJobs+=1;
    }
    const nvda=checkpoints.find(c=>c.symbol==="NVDA")!;
    if(nvda.completeThrough>="2026-09-24T20:00:00.000Z") break;
  }

  const nvda=checkpoints.find(c=>c.symbol==="NVDA")!;
  assert.equal(nvda.completeThrough,"2026-09-24T20:00:00.000Z");
  assert.equal(nvda.version,65);
  assert.equal(nvdaJobs,4);
  assert.ok(selections.length<=16);
});


test("PB-08 post-absence-ack closed-session snapshot reaches Sep25 Regular close in four clean NVDA jobs", () => {
  const observedNow = "2026-09-25T22:14:11.000Z";
  const retentionFloor = "2026-09-24T22:14:11.000Z";
  const frozenFrontier = "2026-09-25T20:00:00.000Z";
  const liveCalendar: MarketCalendarSnapshot = {
    market: "US_EQUITIES",
    dateRange: { startInclusive: "2026-09-25", endExclusive: "2026-09-26" },
    generatedAt: observedNow,
    revision: "pb08-post-absence-ack-closed-session-snapshot",
    sessions: [
      { marketDate:"2026-09-25",sessionKind:"REGULAR",opensAt:"2026-09-25T13:30:00.000Z",closesAt:"2026-09-25T20:00:00.000Z",isShortened:false,calendarRevision:"pb08-post-absence-ack-closed-session-snapshot" },
    ],
  };
  const universe=loadUniverseSnapshot("canary-v0.1");
  const checkpoints:StoredCoverageCheckpoint[]=[
    cp("AMD","REGULAR","stock:iex:raw","2026-09-24T14:50:00.000Z",43),
    cp("QQQ","REGULAR","stock:iex:raw","2026-09-24T14:33:00.000Z",12),
    cp("SPY","REGULAR","stock:iex:raw","2026-09-24T15:10:00.000Z",44),
    cp("NVDA","REGULAR","stock:iex:raw","2026-09-23T18:28:00.000Z",61),
    cp("BTCUSD","ALL_TRADING","crypto:us","2026-09-24T08:13:00.000Z",49),
  ];
  const p=new SchedulePolicy({
    retentionFloor,
    overlapMs:{"1Min":60_000,"15Min":900_000,"1Day":86_400_000},
    finalizationLagMs:{"1Min":60_000,"15Min":120_000,"1Day":1_800_000},
    maxBarsPerJob:100,
    logicalDataVariant:i=>i.providerRoute==="alpaca_crypto_bars"?"crypto:us":"stock:iex:raw",
  });

  let nvdaJobs=0;
  let opportunities=0;
  for(;opportunities<16;opportunities++){
    const jobs=prioritizeAcquisitionJobs(
      p.plan(universe,liveCalendar,checkpoints,new Date(observedNow)),
      checkpoints,
    ).slice(0,2);
    for(const job of jobs){
      const key=job.checkpointExpectations[0]!.coverageKey;
      const item=checkpoints.find(c=>c.coverageKey===key)!;
      item.completeThrough=job.requestedRange.endExclusive;
      item.sourceObservedThrough=job.requestedRange.endExclusive;
      item.version+=1;
      item.state="COMPLETE";
      item.missingRanges=[];
      if(item.symbol==="NVDA") nvdaJobs+=1;
    }
    const nvda=checkpoints.find(c=>c.symbol==="NVDA")!;
    if((nvda.completeThrough ?? "")>=frozenFrontier) break;
  }

  const nvda=checkpoints.find(c=>c.symbol==="NVDA")!;
  assert.equal(nvda.completeThrough,frozenFrontier);
  assert.equal(nvda.version,65);
  assert.equal(nvda.state,"COMPLETE");
  assert.deepEqual(nvda.missingRanges,[]);
  assert.equal(nvdaJobs,4);
  assert.ok(opportunities<16);
});
