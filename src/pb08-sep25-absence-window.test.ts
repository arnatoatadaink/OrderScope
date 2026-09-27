import assert from 'node:assert/strict';
import test from 'node:test';
import { pb08Sep25AbsencesForJob } from './pb08-sep25-absence-window.ts';
import type { AcquisitionJob } from './schedule.ts';
const now=new Date('2026-09-26T07:38:02.000Z');
const job:AcquisitionJob={jobId:'pb08-evidence-test',jobKind:'MARKET_BARS',createdAt:now.toISOString(),
  universeRevision:'stock-monitoring-canary-v0.1',calendarRevision:'alpaca-calendar-v2:60e16a67',
  instruments:[{symbol:'AMD',cadence:'1Min',providerRoute:'alpaca_stock_bars'}],interval:'1Min',
  requestedRange:{startInclusive:'2026-09-25T15:32:00.000Z',endExclusive:'2026-09-25T15:35:00.000Z'},
  sessionScope:'REGULAR',mode:'CATCH_UP',providerRoute:'alpaca_stock_bars',
  checkpointExpectations:[{coverageKey:'AMD|1Min|REGULAR|stock:iex:raw',expectedVersion:45}],attempt:0,dueReason:'FORWARD_COVERAGE'};
test('PB-08 evidence defaults off and expires independently of deployment',()=>{
  assert.deepEqual(pb08Sep25AbsencesForJob(job,undefined,'iex',now),[]);
  assert.deepEqual(pb08Sep25AbsencesForJob(job,'false','iex',now),[]);
  assert.throws(()=>pb08Sep25AbsencesForJob(job,'true','sip',now));
  assert.throws(()=>pb08Sep25AbsencesForJob(job,'true','iex',new Date('2026-09-26T13:30:00.001Z')));
  assert.throws(()=>pb08Sep25AbsencesForJob(job,'invalid','iex',now));
  assert.throws(()=>pb08Sep25AbsencesForJob(job,'true','iex',new Date('invalid')));
});
test('PB-08 selects only twice reproduced absences inside the exact job',()=>{
  const result=pb08Sep25AbsencesForJob(job,'true','iex',now);
  assert.equal(result.length,1);assert.equal(result[0].symbol,'AMD');
  assert.equal(result[0].identityStart,'2026-09-25T15:33:00.000Z');
  assert.match(result[0].evidenceHash,/^[a-f0-9]{64}$/);
  assert.deepEqual(pb08Sep25AbsencesForJob({...job,sessionScope:'PREMARKET'},'true','iex',now),[]);
  assert.deepEqual(pb08Sep25AbsencesForJob({...job,logicalDataVariant:'stock:iex:split'},'true','iex',now),[]);
  assert.deepEqual(pb08Sep25AbsencesForJob({...job,interval:'15Min'},'true','iex',now),[]);
  assert.deepEqual(pb08Sep25AbsencesForJob({...job,instruments:[{symbol:'AMD',cadence:'15Min',providerRoute:'alpaca_stock_bars'}]},'true','iex',now),[]);
  assert.deepEqual(pb08Sep25AbsencesForJob({...job,instruments:[{symbol:'NVDA',cadence:'1Min',providerRoute:'alpaca_stock_bars'}]},'true','iex',now),[]);
  assert.deepEqual(pb08Sep25AbsencesForJob({...job,requestedRange:{startInclusive:'2026-09-25T15:34:00.000Z',endExclusive:'2026-09-25T15:35:00.000Z'}},'true','iex',now),[]);
  assert.deepEqual(pb08Sep25AbsencesForJob({...job,requestedRange:{startInclusive:'2026-09-26T15:32:00.000Z',endExclusive:'2026-09-26T15:35:00.000Z'}},'true','iex',now),[]);
});
