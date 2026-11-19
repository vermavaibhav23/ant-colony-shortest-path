// Ant System: same graph, alpha=1, beta=1, rho=0.3, Q=10 as the desktop demo.
export const edges=[['A','D',8],['D','G',5],['G','J',8],['B','E',9],['E','H',6],['H','K',3],['C','F',8],['F','I',7],['I','L',2],['A','B',3],['B','C',3],['D','E',4],['E','F',9],['G','H',2],['H','I',8],['J','K',5],['K','L',6],['S','A',6],['S','B',7],['S','C',7],['J','T',3],['K','T',8],['L','T',9]];
export const key=(a,b)=>[a,b].sort().join('-');
export const graph={};
for(const [a,b,d] of edges){(graph[a]??={})[b]=d;(graph[b]??={})[a]=d;}
export function rng(seed){return ()=>{let t=seed+=0x6D2B79F5;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};}
export class Colony{
 constructor(seed=1,ants=40){this.random=rng(seed);this.ants=ants;this.tau=Object.fromEntries(edges.map(([a,b])=>[key(a,b),1]));this.round=0;this.best=null;this.pending=null;this.history=[];}
 explore(){if(this.pending)throw Error('Apply pending scores first');const attempts=[];
  for(let i=0;i<this.ants;i++){const path=['S'];let cost=0;while(path.at(-1)!=='T'){const u=path.at(-1),choices=Object.keys(graph[u]).filter(v=>!path.includes(v));if(!choices.length)break;const weights=choices.map(v=>this.tau[key(u,v)]/graph[u][v]);let r=this.random()*weights.reduce((a,b)=>a+b,0),chosen=choices.at(-1);for(let j=0;j<choices.length;j++){r-=weights[j];if(r<0){chosen=choices[j];break;}}cost+=graph[u][chosen];path.push(chosen);}attempts.push({path,cost,success:path.at(-1)==='T'});}
  const rows=Object.fromEntries(Object.entries(this.tau).map(([k,old])=>[k,{old,remaining:Math.max(1e-12,old*.7),reward:0,count:0}]));
  for(const ant of attempts.filter(a=>a.success))for(let j=1;j<ant.path.length;j++){const row=rows[key(ant.path[j-1],ant.path[j])];row.reward+=10/ant.cost;row.count++;}
  for(const row of Object.values(rows))row.new=row.remaining+row.reward;
  this.pending={attempts,rows};return this.pending;
 }
 apply(){if(!this.pending)return false;for(const ant of this.pending.attempts)if(ant.success&&(!this.best||ant.cost<this.best.cost))this.best={path:[...ant.path],cost:ant.cost};for(const [k,r] of Object.entries(this.pending.rows))this.tau[k]=r.new;this.round++;this.history.push(this.best?.cost??null);this.pending=null;return true;}
}
export function position(ant,distance){if(distance<0)return {u:'S',v:'S',f:0,done:false};for(let i=1;i<ant.path.length;i++){const u=ant.path[i-1],v=ant.path[i],d=graph[u][v];if(distance<d)return {u,v,f:distance/d,done:false};distance-=d;}return {u:ant.path.at(-1),v:ant.path.at(-1),f:0,done:true};}
