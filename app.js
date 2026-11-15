const $ = id => document.getElementById(id);
const api = async (url, options={}) => {
  const res = await fetch(url, {headers:{'Content-Type':'application/json'}, ...options});
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Something went wrong');
  return data;
};
const dayOrder = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
function notify(message){ alert(message); }
function setDate(){
  $('today').textContent = new Intl.DateTimeFormat('en-IN',{weekday:'short',day:'numeric',month:'short',year:'numeric'}).format(new Date());
}
function examInfo(settings){
  if(!settings.exam_date){$('examDays').textContent='—';$('examBig').textContent='—';$('examName').textContent='Add your exam details';$('examLabel').textContent='Add an exam date';return;}
  const diff=Math.ceil((new Date(settings.exam_date+'T00:00:00')-new Date(new Date().toDateString()))/86400000);
  const label=diff<0?'Exam date passed':diff===0?'Your exam is today':`${diff} days`;
  $('examDays').textContent=label;$('examBig').textContent=diff<0?'Done':diff===0?'Today':`${diff} Days`;
  $('examName').textContent=settings.exam_subject||'Upcoming exam';$('examLabel').textContent=(settings.exam_subject||'Your exam')+' · '+settings.exam_date;
}
function renderSubjects(subjects){
  $('subjectCount').textContent=subjects.length;
  $('subjectList').innerHTML=subjects.length?subjects.map(s=>`<span class="subject-tag">${escapeHtml(s.name)} <small>Difficulty ${s.difficulty}/5</small><button title="Remove subject" onclick="removeSubject(${s.id})">×</button></span>`).join(''):'<p class="empty">No subjects yet. Add your first subject.</p>';
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function renderTasks(tasks){
  $('taskCount').textContent=tasks.length;
  if(!tasks.length){$('timetableBody').innerHTML='<tr><td colspan="4" class="empty">Your timetable will appear here after generation.</td></tr>';return;}
  tasks.sort((a,b)=>dayOrder.indexOf(a.day)-dayOrder.indexOf(b.day)||a.start.localeCompare(b.start));
  $('timetableBody').innerHTML=tasks.map(t=>`<tr class="${t.done?'done-row':''}"><td><b>${t.day}</b></td><td class="task-time">${t.start} – ${t.end}</td><td class="task-name">${escapeHtml(t.subject)} <small>· ${t.kind}</small></td><td><button class="status-btn ${t.done?'done':''}" onclick="toggleTask(${t.id})">${t.done?'✓ Completed':'Mark done'}</button></td></tr>`).join('');
}
async function load(){
  const d=await api('/api/data');
  $('greeting').textContent=`Hello, ${d.settings.name||'Student'}! 👋`;
  $('name').value=d.settings.name;$('hours').value=d.settings.hours;$('start').value=d.settings.start_time;$('end').value=d.settings.end_time;
  $('examDate').value=d.settings.exam_date;$('examSubject').value=d.settings.exam_subject;
  examInfo(d.settings);renderSubjects(d.subjects);renderTasks(d.tasks);
  $('progressValue').textContent=d.progress+'%';$('progressText').textContent=d.progress+'%';$('progressBar').style.width=d.progress+'%';$('progressFill').style.width=d.progress+'%';
  $('completedCount').textContent=d.completed;$('remainingCount').textContent=d.total-d.completed;
  await loadTips();
}
async function loadTips(){const d=await api('/api/recommendations');$('tips').innerHTML=d.tips.map(t=>`<li>${escapeHtml(t)}</li>`).join('');}
$('settingsForm').addEventListener('submit',async e=>{e.preventDefault();try{await api('/api/settings',{method:'POST',body:JSON.stringify({name:$('name').value,hours:$('hours').value,start_time:$('start').value,end_time:$('end').value,exam_date:$('examDate').value,exam_subject:$('examSubject').value})});await load();notify('Study preferences saved!');}catch(err){notify(err.message);}});
$('subjectForm').addEventListener('submit',async e=>{e.preventDefault();try{await api('/api/subjects',{method:'POST',body:JSON.stringify({name:$('subjectName').value,difficulty:$('difficulty').value,priority:$('priority').value})});$('subjectName').value='';await load();}catch(err){notify(err.message);}});
async function removeSubject(id){if(!confirm('Remove this subject?'))return;await api('/api/subjects/'+id,{method:'DELETE'});await load();}
async function generate(){try{const d=await api('/api/generate',{method:'POST',body:'{}'});await load();notify(`Your timetable is ready! ${d.count} sessions created.`);}catch(err){notify(err.message);}}
async function toggleTask(id){await api('/api/tasks/'+id,{method:'PATCH'});await load();}
$('generateBtn').addEventListener('click',generate);$('quickGenerate').addEventListener('click',generate);
$('refreshTips').addEventListener('click',loadTips);$('quickTips').addEventListener('click',()=>{loadTips();$('ai').scrollIntoView({behavior:'smooth'});});
setDate();load().catch(e=>notify(e.message));
