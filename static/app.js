const state={collection:null,course:{course:{},collections:[]},history:[]};
const materials=document.querySelector('#materials');
const messages=document.querySelector('#messages');
const welcome=document.querySelector('#welcome');
const form=document.querySelector('#chat-form');
const input=document.querySelector('#message');
const send=document.querySelector('#send');
const tabs=document.querySelector('#tabs');

function esc(text){const node=document.createElement('div');node.textContent=text;return node.innerHTML}
function activeCollection(){return state.course.collections.find(item=>item.id===state.collection)||{items:[]}}
function renderTabs(){
  tabs.innerHTML=state.course.collections.map((item,index)=>`<button class="tab ${index===0?'active':''}" data-tab="${esc(item.id)}">${esc(item.title)}</button>`).join('');
  tabs.querySelectorAll('.tab').forEach(tab=>tab.onclick=()=>{tabs.querySelector('.active')?.classList.remove('active');tab.classList.add('active');state.collection=tab.dataset.tab;renderMaterials()});
}
function renderMaterials(){
  materials.innerHTML=activeCollection().items.map(item=>`<button class="material" data-file="/materials/${encodeURI(item.file)}"><strong>${esc(item.title)}</strong><small>${esc(item.file.split('/').pop())}</small></button>`).join('');
  materials.querySelectorAll('.material').forEach(button=>button.onclick=()=>window.open(button.dataset.file,'_blank'));
}
function addMessage(role,text,sources=[]){
  welcome.style.display='none';messages.style.display='block';
  const item=document.createElement('article');item.className=`message ${role}`;item.textContent=text;
  if(sources.length){const source=document.createElement('div');source.className='sources';source.textContent='Sources: '+sources.map(s=>`${s.id} p.${s.page}`).join(' · ');item.appendChild(source)}
  messages.appendChild(item);messages.scrollTop=messages.scrollHeight;return item;
}
async function ask(text){
  addMessage('user',text);input.value='';send.disabled=true;const waiting=addMessage('assistant','Searching course materials...');
  try{const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,history:state.history})});const data=await response.json();if(!response.ok)throw new Error(data.error||'Request failed');waiting.remove();addMessage('assistant',data.answer,data.sources||[]);state.history.push({role:'user',content:text},{role:'assistant',content:data.answer})}
  catch(error){waiting.textContent=error.message;waiting.classList.add('error')}finally{send.disabled=false;input.focus()}
}
document.querySelectorAll('[data-prompt]').forEach(button=>button.onclick=()=>ask(button.dataset.prompt));
form.onsubmit=event=>{event.preventDefault();const text=input.value.trim();if(text)ask(text)};
input.onkeydown=event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();form.requestSubmit()}};

Promise.all([fetch('/api/course').then(r=>r.json()),fetch('/api/status').then(r=>r.json())]).then(([course,status])=>{
  state.course=course;state.collection=course.collections?.[0]?.id||null;renderTabs();renderMaterials();
  document.querySelector('#course-title').textContent=course.course?.title||'Study Desk';
  document.querySelector('#course-subtitle').textContent=(course.course?.subtitle||'Course-grounded learning').toUpperCase();
  const itemCount=(course.collections||[]).reduce((sum,item)=>sum+item.items.length,0);
  document.querySelector('#status').textContent=`${itemCount} items · ${status.model||status.provider}${status.agent_configured?'':' · configure agent'}`;
});
