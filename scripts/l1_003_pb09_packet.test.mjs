import test from 'node:test';
import assert from 'node:assert/strict';
import {assessPhaseBEntry,freezePauseGap} from './l1_003_pb09_packet.mjs';
const session={sessionKind:'REGULAR',opensAt:'2026-09-28T13:30:00.000Z',closesAt:'2026-09-28T20:00:00.000Z'};
const cp={coverage_key:'NVDA|1Min|REGULAR|stock:iex:raw',version:70,state:'COMPLETE',missing_ranges_json:'[]',
  complete_through:'2026-09-28T14:00:00.000Z',source_observed_through:'2026-09-28T14:00:00.000Z',blocker_json:null,retry_not_before:null};
const input={observedNow:'2026-09-28T14:01:19.000Z',health:{mode:'shadow',feed:'iex',news:{mode:'disabled'}},calendar:{sessions:[session]},checkpoints:[cp],unresolvedAttempts:0};
test('closed market preserves accepted work without inventing an entry',()=>{
  const r=assessPhaseBEntry({...input,observedNow:'2026-09-26T11:21:15.000Z'});
  assert.equal(r.status,'WAITING_ACTIVE_MARKET_SESSION');assert.equal(r.candidate,null);assert.equal(r.nextSession,session);assert.equal(r.remoteMutation,false);
});
test('active entry must equal authoritative finalized frontier',()=>{
  assert.equal(assessPhaseBEntry(input).status,'ENTRY_EVIDENCE_READY_NOT_AUTHORIZED');
  assert.equal(assessPhaseBEntry({...input,checkpoints:[{...cp,complete_through:'2026-09-25T20:00:00.000Z',source_observed_through:'2026-09-25T20:00:00.000Z'}]}).status,'CURRENT_CHECKPOINT_REQUIRED');
  assert.throws(()=>assessPhaseBEntry({...input,unresolvedAttempts:1}));
  assert.throws(()=>assessPhaseBEntry({...input,checkpoints:[{...cp,state:'PARTIAL'}]}));
  assert.throws(()=>assessPhaseBEntry({...input,health:{...input.health,mode:'live'}}));
});
test('only unchanged checkpoint and newly finalized pause gap qualify',()=>{
  const args={session,beforePause:cp,beforeResume:cp,pauseStart:'2026-09-28T14:01:19.000Z',resumeAt:'2026-09-28T14:04:19.000Z'};
  assert.deepEqual(freezePauseGap(args),{startInclusive:'2026-09-28T14:00:00.000Z',endExclusive:'2026-09-28T14:03:00.000Z',expectedFreshMinutes:3});
  assert.throws(()=>freezePauseGap({...args,beforeResume:{...cp,version:71}}));
  assert.throws(()=>freezePauseGap({...args,pauseStart:'2026-09-28T14:02:19.000Z'}));
  assert.throws(()=>freezePauseGap({...args,resumeAt:'2026-09-28T14:07:19.000Z'}));
  assert.throws(()=>freezePauseGap({...args,resumeAt:'2026-09-28T14:01:30.000Z'}));
  assert.throws(()=>freezePauseGap({...args,pauseStart:'2026-09-28T14:01:19Z'}));
  assert.throws(()=>freezePauseGap({...args,resumeAt:'2026-09-28T20:00:00.000Z'}));
  assert.throws(()=>freezePauseGap({...args,beforePause:{...cp,coverage_key:'BTCUSD|1Min|ALL_TRADING|crypto:us'}}));
});
