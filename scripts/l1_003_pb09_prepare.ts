import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {AlpacaMarketCalendarProvider} from '../src/calendar.ts';
import {assessPhaseBEntry} from './l1_003_pb09_packet.mjs';
const directory=process.argv[2];
if(!directory)throw new Error('snapshot directory required');
const observedNow=new Date().toISOString();
const keyId=process.env.ALPACA_API_KEY,secretKey=process.env.ALPACA_API_SECRET;
if(!keyId||!secretKey)throw new Error('Alpaca calendar credentials unavailable');
const start=new Date(Date.parse(observedNow)-2*86_400_000).toISOString().slice(0,10);
const end=new Date(Date.parse(observedNow)+7*86_400_000).toISOString().slice(0,10);
const calendar=await new AlpacaMarketCalendarProvider({credentials:{keyId,secretKey}}).getCalendar(start,end);
const health=JSON.parse(fs.readFileSync(`${directory}/health.json`,'utf8'));
const groups=JSON.parse(fs.readFileSync(`${directory}/state.json`,'utf8'));
if(!Array.isArray(groups)||groups.some(g=>g.success!==true))throw new Error('D1 snapshot failed');
const checkpoints=groups[0].results,unresolvedAttempts=groups[1].results[0].unresolved_canary_attempts;
if(checkpoints.length!==5||new Set(checkpoints.map(c=>c.coverage_key)).size!==5
  ||groups[2].results[0].control_path_ok!==1||groups.some(g=>g.meta?.changed_db!==false))throw new Error('incomplete or non-read-only snapshot');
const deployments=JSON.parse(fs.readFileSync(`${directory}/deployments.json`,'utf8'));
const deployment=deployments.sort((a,b)=>Date.parse(b.created_on)-Date.parse(a.created_on))[0];
if(!deployment||deployment.versions.length!==1||deployment.versions[0].percentage!==100)throw new Error('ambiguous deployment identity');
const lagMinutes=1; // checked against checked-in live-canary config by launcher
const assessment=assessPhaseBEntry({observedNow,health,calendar,checkpoints,unresolvedAttempts,lagMinutes});
const evidence={observedNow,remoteMutation:false,release:fs.readFileSync(`${directory}/release.txt`,'utf8').trim(),
  worktree:fs.readFileSync(`${directory}/worktree.txt`,'utf8').trim(),
  configSha256:createHash('sha256').update(fs.readFileSync('wrangler.jsonc')).digest('hex'),
  deploymentId:deployment.id,workerVersion:deployment.versions[0].version_id,
  lagMinutes,health,calendar,checkpoints,unresolvedAttempts,assessment};
fs.writeFileSync(`${directory}/packet.json`,JSON.stringify(evidence,null,2)+'\n');
console.log(JSON.stringify(assessment,null,2));
