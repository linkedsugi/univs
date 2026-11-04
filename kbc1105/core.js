import {APP_ID,VERSION,fields,pages,sampleProfiles} from './data.js';
export const MAX_BYTES=2_000_000;
export const escapeHTML=(s)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function fresh(){return{appId:APP_ID,version:VERSION,savedAt:null,answers:Object.fromEntries(Object.values(fields).map(f=>[f.id,f.default])),completed:[],currentPage:0,demo:false,sampleId:null};}
export function validate(input){
 if(!input||typeof input!=='object'||Array.isArray(input)||input.appId!==APP_ID||input.version!==VERSION)throw Error('이 워크북의 버전 1 백업이 아닙니다. 현재 내용은 바뀌지 않았습니다.');
 if(!input.answers||typeof input.answers!=='object'||Array.isArray(input.answers))throw Error('답안 형식이 올바르지 않습니다.');
 const clean=fresh();
 for(const key of Object.keys(input.answers))if(!Object.hasOwn(fields,key))throw Error('알 수 없는 입력 항목이 있습니다.');
 for(const [key,f] of Object.entries(fields)){
  const v=input.answers[key];
  if(f.type==='checkbox'){if(typeof v!=='boolean')throw Error(`${f.label}: 체크 값이 올바르지 않습니다.`);}
  else{if(typeof v!=='string'||v.length>10000)throw Error(`${f.label}: 입력 형식 또는 길이를 확인해 주세요.`);
   if(f.type==='select'&&v!==''&&!f.options.includes(v))throw Error(`${f.label}: 선택지가 올바르지 않습니다.`);
   if(f.type==='integer'&&v!==''&&(!/^\d+$/.test(v)||Number(v)>1_000_000))throw Error(`${f.label}: 0 이상의 정수를 사용하세요.`);
  }clean.answers[key]=v;
 }
 if(!Array.isArray(input.completed)||input.completed.some(n=>!Number.isInteger(n)||n<1||n>12)||new Set(input.completed).size!==input.completed.length)throw Error('완료 표시 형식이 올바르지 않습니다.');
 clean.completed=[...input.completed];
 if(!Number.isInteger(input.currentPage)||input.currentPage<0||input.currentPage>13)throw Error('페이지 정보가 올바르지 않습니다.');
 if(typeof input.demo!=='boolean')throw Error('예시 표시가 올바르지 않습니다.');
 clean.currentPage=input.currentPage;clean.demo=input.demo;
 if(input.sampleId!==undefined&&input.sampleId!==null&&!sampleProfiles.some(p=>p.id===input.sampleId))throw Error('샘플 식별자가 올바르지 않습니다.');
 clean.sampleId=input.sampleId??null;
 if(input.savedAt!==null&&(typeof input.savedAt!=='string'||!Number.isFinite(Date.parse(input.savedAt))))throw Error('저장 시각이 올바르지 않습니다.');
 clean.savedAt=input.savedAt;return clean;
}
export function parseBackup(text){if(new TextEncoder().encode(text).length>MAX_BYTES)throw Error('2MB 이하의 JSON 파일을 선택해 주세요.');return validate(JSON.parse(text));}
export const pct=v=>v===null?'계산 불가':`${(v*100).toFixed(1)}%`;
export function metrics(a){const keys=['tp','fn','fp','tn'];if(keys.some(k=>a[k]===''||!/^\d+$/.test(a[k])||Number(a[k])>1_000_000))return null;const [tp,fn,fp,tn]=keys.map(k=>Number(a[k]));return{total:tp+fn+fp+tn,accuracy:tp+fn+fp+tn?(tp+tn)/(tp+fn+fp+tn):null,precision:tp+fp?tp/(tp+fp):null,recall:tp+fn?tp/(tp+fn):null};}
export function ragMetrics(a){let source=0,wrong=0,hallucinated=0,evaluated=0;for(let i=0;i<20;i++){if(a[`rag_${i}_source`]==='맞음')source++;const v=a[`rag_${i}_result`];if(v)evaluated++;if(v==='× 틀림')wrong++;if(v==='지어냄')hallucinated++;}const answered=a.rag_answered===''?null:Number(a.rag_answered);const valid=Number.isInteger(answered)&&answered>=0&&answered<=20&&answered>=source;return{source,wrong,hallucinated,evaluated,answered,valid,sourceRate:valid&&answered>0?source/answered:null,errorRate:(wrong+hallucinated)/20};}
export function warnings(s){const a=s.answers,w=[];const design=Array.from({length:6},(_,i)=>`design_${i}`).filter(k=>!a[k].trim()).length;const frontier=Array.from({length:5},(_,i)=>`frontier_${i}`).filter(k=>!a[k].trim()).length;if(design)w.push(`설계서 ${design}칸 미작성`);if(frontier)w.push(`후보서 ${frontier}칸 미작성`);if(!a.frontier_gate.trim())w.push('학생 공개 전 잠금 게이트 미작성');if(Array.from({length:5},(_,i)=>a[`diagnostic_${i}_after`]).some(v=>!v))w.push('사후 진단 미완료');if(a.rag_answered!==''&&!ragMetrics(a).valid)w.push('RAG 답한 수는 0~20이며 출처 맞음 수 이상이어야 합니다.');if(Object.values(a).some(v=>typeof v==='string'&&v.includes('확인 필요')))w.push('‘확인 필요’ 표시가 남아 있습니다.');if(s.demo)w.push('연습용 예시가 적용된 상태입니다.');return w;}
export function demo(id=sampleProfiles[0].id,identity={}){const p=sampleProfiles.find(x=>x.id===id);if(!p)throw Error('알 수 없는 샘플입니다.');const s=fresh();Object.assign(s.answers,p.values);for(const k of ['name','department'])if(typeof identity[k]==='string')s.answers[k]=identity[k];s.demo=true;s.sampleId=p.id;s.currentPage=10;return s;}
export function designDraft(a){return{design_0:a.method_0_0||a.baseline_0_0||a.opening_judgment,design_1:a.method_0_4,design_2:a.method_0_2,design_3:[a.baseline_0_4,a.baseline_0_2,a.rag_delegation&&`RAG 판단 ${a.rag_delegation}`].filter(Boolean).join('\n')};}
export function frontierDraft(a){return{frontier_0:a.design_0,frontier_1:a.design_1,frontier_3:a.design_4,frontier_4:a.design_3,frontier_gate:a.design_5};}
export function pageFields(page){const ids=[];function walk(x){if(!x||typeof x!=='object')return;if(x.kind==='field')ids.push(x.id);else for(const v of Object.values(x))if(Array.isArray(v))v.forEach(walk);else if(v&&typeof v==='object')walk(v);}page.blocks.forEach(walk);return ids;}
export function written(s,page){return pageFields(page).filter(k=>s.answers[k]!==fields[k].default&&s.answers[k]!=='').length;}
