// Read-only provider evidence generation. Does not authorize remote mutation.
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const headers={'APCA-API-KEY-ID':process.env.ALPACA_API_KEY,'APCA-API-SECRET-KEY':process.env.ALPACA_API_SECRET};
if(!headers['APCA-API-KEY-ID'] || !headers['APCA-API-SECRET-KEY']) throw new Error('credentials missing');
const records=[];
for(const symbol of ['AMD','QQQ','SPY','NVDA']) {
  const start=symbol==='AMD'?'2026-09-25T15:32:00.000Z':'2026-09-25T15:10:00.000Z';
  const end='2026-09-25T20:00:00.000Z';
  const observations=[];
  for(let n=0;n<2;n++) {
    const url=new URL(`https://data.alpaca.markets/v2/stocks/${symbol}/bars`);
    for(const [k,v] of Object.entries({timeframe:'1Min',start,end,adjustment:'raw',feed:'iex',limit:'1000',sort:'asc'}))url.searchParams.set(k,v);
    const response=await fetch(url,{headers});
    if(!response.ok)throw new Error(`provider HTTP ${response.status}`);
    const body=await response.text();const data=JSON.parse(body);
    if(!Array.isArray(data.bars)||data.next_page_token)throw new Error('incomplete provider response');
    const times=new Set(data.bars.map(b=>Date.parse(b.t)));const missing=[];
    for(let t=Date.parse(start);t<Date.parse(end);t+=60_000)if(!times.has(t))missing.push(new Date(t).toISOString());
    observations.push({observedAt:new Date().toISOString(),responseSha256:createHash('sha256').update(body).digest('hex'),returnedStarts:data.bars.map(b=>new Date(b.t).toISOString()),missing});
  }
  if(JSON.stringify(observations[0].missing)!==JSON.stringify(observations[1].missing))throw new Error('provider absence changed between observations');
  records.push({symbol,start,end,observations});
}
const evidence={feed:'iex',adjustment:'raw',session:'2026-09-25',records};
const serialized=JSON.stringify(evidence,null,2);
fs.writeFileSync('docs/work-management/local-corporate-intelligence/L1-003_PB08_SEP25_PROVIDER_ABSENCE_EVIDENCE.json',serialized+'\n');
const evidenceHash=createHash('sha256').update(serialized).digest('hex');
const absences=records.flatMap(r=>r.observations[0].missing.map(identityStart=>({symbol:r.symbol,identityStart,reason:'REPRODUCIBLE_PROVIDER_ABSENCE',evidenceHash})));
fs.writeFileSync('src/pb08-sep25-absence-evidence.ts', '// Generated from two read-only IEX observations per symbol.\nexport const PB08_SEP25_ABSENCES = '+JSON.stringify(absences,null,2)+' as const;\n');
console.log(JSON.stringify({remoteMutation:false,evidenceHash,counts:records.map(r=>({symbol:r.symbol,missing:r.observations[0].missing.length}))}));
