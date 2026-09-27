// Pure, read-only Phase B entry assessment. No mutation or implicit authority.
export function canonical(value) {
  const time=Date.parse(value);
  if(!Number.isFinite(time)||new Date(time).toISOString()!==value)throw new Error('canonical UTC required');
  return time;
}
export function finalizedFrontier(session,now,lagMinutes=1) {
  const open=canonical(session.opensAt),close=canonical(session.closesAt);
  return new Date(Math.max(open,Math.min(close,Math.floor((canonical(now)-lagMinutes*60_000)/60_000)*60_000))).toISOString();
}
export function assessPhaseBEntry({observedNow,health,calendar,checkpoints,unresolvedAttempts,lagMinutes=1}) {
  const time=canonical(observedNow);
  if(health.mode!=='shadow'||health.feed!=='iex'||health.news?.mode!=='disabled')throw new Error('unsafe baseline');
  if(unresolvedAttempts!==0)throw new Error('unresolved canary attempts');
  const sessions=calendar.sessions.filter(s=>s.sessionKind==='REGULAR').sort((a,b)=>canonical(a.opensAt)-canonical(b.opensAt));
  const active=sessions.find(s=>canonical(s.opensAt)<=time&&time<canonical(s.closesAt));
  const next=sessions.find(s=>canonical(s.opensAt)>time);
  const healthy=c=>c.state==='COMPLETE'&&c.missing_ranges_json==='[]'&&c.blocker_json===null&&c.retry_not_before===null
    &&c.complete_through===c.source_observed_through;
  if(checkpoints.some(c=>!healthy(c)))throw new Error('unreconciled competition checkpoint');
  if(!active)return {status:'WAITING_ACTIVE_MARKET_SESSION',nextSession:next??null,candidate:null,remoteMutation:false};
  const frontier=finalizedFrontier(active,observedNow,lagMinutes);
  const candidates=checkpoints.filter(c=>c.coverage_key.endsWith('|1Min|REGULAR|stock:iex:raw')
    &&healthy(c)&&c.complete_through===frontier&&canonical(c.complete_through)>canonical(active.opensAt));
  candidates.sort((a,b)=>a.coverage_key.localeCompare(b.coverage_key));
  return {status:candidates.length?'ENTRY_EVIDENCE_READY_NOT_AUTHORIZED':'CURRENT_CHECKPOINT_REQUIRED',
    activeSession:active,finalizedFrontier:frontier,candidate:candidates[0]??null,remoteMutation:false};
}
export function freezePauseGap({session,beforePause,beforeResume,pauseStart,resumeAt,lagMinutes=1}) {
  const start=canonical(pauseStart),end=canonical(resumeAt);
  if(end<=start||end-start>300_000)throw new Error('pause must be positive and at most five minutes');
  if(start<canonical(session.opensAt)||end>=canonical(session.closesAt))throw new Error('pause must stay inside active REGULAR session');
  for(const cp of [beforePause,beforeResume]){
    if(!cp.coverage_key.endsWith('|1Min|REGULAR|stock:iex:raw'))throw new Error('pause candidate must be equity 1Min REGULAR IEX');
    if(cp.state!=='COMPLETE'||cp.missing_ranges_json!=='[]'||cp.blocker_json!==null||cp.retry_not_before!==null
      ||cp.complete_through!==cp.source_observed_through)throw new Error('unhealthy pause checkpoint');
    canonical(cp.complete_through);
  }
  if(beforePause.coverage_key!==beforeResume.coverage_key||beforePause.version!==beforeResume.version
    ||beforePause.complete_through!==beforeResume.complete_through)throw new Error('checkpoint changed while paused');
  if(beforePause.complete_through!==finalizedFrontier(session,pauseStart,lagMinutes))throw new Error('pre-existing gap at pause entry');
  const target=finalizedFrontier(session,resumeAt,lagMinutes);
  if(canonical(target)<=canonical(beforeResume.complete_through))throw new Error('pause created no finalized gap');
  return {startInclusive:beforeResume.complete_through,endExclusive:target,
    expectedFreshMinutes:(canonical(target)-canonical(beforeResume.complete_through))/60_000};
}
