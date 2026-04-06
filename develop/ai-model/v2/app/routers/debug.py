from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.persona_registry import list_active_personas

router = APIRouter(tags=["debug"])

DEFAULT_USER_ID = "dev_tester"
DEFAULTS = {
    "persona": "default",
    "mbti": "ISTJ",
    "goal": "fat_loss",
    "activity_level": "moderate",
    "diet_type": "balanced",
    "gender": "male",
    "age": "25",
    "weight": "72.5",
    "height": "175",
    "allergies": "none",
    "injury_history": "none",
}

EXAMPLES: dict[str, list[tuple[str, str]]] = {
    "Casual": [("Light", "오늘 운동하기 너무 귀찮아."), ("Check", "오늘 컨디션이 좀 애매한데 운동 가도 될까?")],
    "Care": [("Stress", "요즘 운동 의욕이 너무 없어서 속상해."), ("Diet", "식단을 계속 실패해서 자꾸 자책하게 돼.")],
    "Record": [("Weight", "내 몸무게 71.8kg으로 기록해줘."), ("Injury", "무릎 통증이 있어서 부상 이력에 추가해줘.")],
    "Plan": [("Workout", "이번 주 주 4회 근비대 운동 계획 짜줘."), ("Diet", "감량용 일주일 식단 계획 만들어줘.")],
    "Modify": [("Schedule", "목요일 하체 운동은 토요일로 바꿔줘."), ("Intensity", "이번 주 계획 강도를 조금 낮춰줘.")],
    "Approve": [("Approve", "좋아, 그 계획으로 진행해줘."), ("Apply", "응, 이대로 반영해줘.")],
    "Info": [("Protein", "감량 중에도 단백질을 많이 먹어도 돼?"), ("HIIT", "HIIT를 주 몇 번 하는 게 좋아?")],
    "Safety": [("Chest", "운동하다가 가슴이 조여오고 숨이 차."), ("Dizzy", "운동 중에 어지럽고 쓰러질 것 같아.")],
    "Fallback": [("Ambiguous", "그거 좀 다르게 해줘."), ("Context", "아까 말한 걸 기준으로 다시 해줘.")],
}

html_template = """
<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Hub v2 Debug</title>
<style>
:root{--bg:#0a1020;--panel:#15223c;--line:#2c3e66;--text:#d9e1f1;--muted:#8a98b5;--strong:#f8fbff;--primary:#5f84ff;--user:#4161e1;--bot:#10192f;--warn:#fbbf24}
*{box-sizing:border-box}body{margin:0;height:100vh;overflow:hidden;font-family:Inter,'Segoe UI',sans-serif;background:linear-gradient(180deg,#09101f 0,#0d1425 100%);color:var(--text)}
.page{height:100vh;padding:18px;display:grid;grid-template-columns:minmax(760px,1.45fr) minmax(430px,.9fr);gap:18px}
.left{min-height:0;display:grid;grid-template-rows:auto minmax(0,1fr);gap:14px}.hero,.panel,.chat{background:rgba(21,34,60,.94);border:1px solid var(--line);border-radius:18px}
.hero{padding:18px 22px}.hero h1{margin:0;font-size:1.14rem;color:var(--strong)}.hero p{margin:8px 0 0;color:var(--muted);font-size:.86rem;line-height:1.55}
.work{min-height:0;overflow:auto;padding-right:4px;display:grid;grid-template-columns:280px minmax(0,1fr);gap:14px}.stack{display:grid;gap:14px;align-content:start}
.panel{min-height:0;display:flex;flex-direction:column}.ph{padding:16px 18px 12px;border-bottom:1px solid rgba(255,255,255,.05)}.ey{font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:800;margin-bottom:8px}.ph h2{margin:0;font-size:1rem;color:var(--strong)}.ph p{margin:8px 0 0;font-size:.82rem;color:var(--muted);line-height:1.5}.pb{padding:16px 18px 18px;min-height:0;overflow:auto}
.field{display:flex;flex-direction:column;gap:7px}.field label{font-size:.8rem;font-weight:700}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.span3{grid-column:span 3}
input,select{width:100%;padding:11px 12px;border-radius:12px;border:1px solid var(--line);background:#0d162a;color:var(--strong);font-size:.92rem;outline:none}input:focus,select:focus{border-color:var(--primary)}
.meta{background:rgba(13,22,42,.88);border:1px solid var(--line);border-radius:14px;padding:14px}.meta strong{display:block;margin-bottom:8px;color:var(--strong)}.meta code{color:#b8d4ff;word-break:break-all}.hint{font-size:.78rem;line-height:1.55;color:var(--muted)}
.row{display:flex;flex-wrap:wrap;gap:10px}.btn{padding:11px 14px;border-radius:12px;font-size:.86rem;font-weight:800;cursor:pointer;border:1px solid transparent}.btn.s{background:#0d162a;color:var(--text);border-color:var(--line)}.btn.p{background:var(--primary);color:#fff}
.examples{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.group{background:rgba(13,22,42,.74);border:1px solid var(--line);border-radius:14px;padding:12px}.gt{font-size:.82rem;font-weight:800;color:var(--strong);margin-bottom:10px}.gbtns{display:flex;flex-wrap:wrap;gap:8px}.eb{padding:8px 10px;border-radius:999px;border:1px solid var(--line);background:#13213f;color:var(--text);font-size:.78rem;font-weight:800;cursor:pointer}
.chat-pane{min-height:0;overflow:hidden}.chat{height:100%;min-height:0;display:grid;grid-template-rows:auto minmax(0,1fr) auto auto;overflow:hidden}.ch{padding:16px 18px 12px;border-bottom:1px solid rgba(255,255,255,.05);display:flex;justify-content:space-between;align-items:center;gap:12px}.ch h2{margin:0;font-size:1rem;color:var(--strong)}.ch p{margin:6px 0 0;font-size:.8rem;color:var(--muted)}.pill{padding:8px 10px;border-radius:999px;background:rgba(95,132,255,.14);color:#bdd0ff;font-size:.79rem;font-weight:800;white-space:nowrap}
.history{min-height:0;overflow-y:auto;overscroll-behavior:contain;scrollbar-gutter:stable;padding:16px 18px 20px;display:flex;flex-direction:column;gap:16px}.msg{display:flex;flex-direction:column;gap:8px;max-width:88%}.msg.user{align-self:flex-end;align-items:flex-end}.msg.bot{align-self:flex-start;align-items:flex-start}.bubble{padding:14px 16px;border-radius:18px;line-height:1.62;font-size:.93rem}.user .bubble{background:var(--user);color:#fff;border-bottom-right-radius:6px}.bot .bubble{background:var(--bot);color:var(--strong);border:1px solid var(--line);border-bottom-left-radius:6px}
.dbg{width:100%;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:rgba(13,22,42,.94)}.dbgh{display:flex;justify-content:space-between;padding:10px 14px;background:#1a2849;color:var(--primary);font-size:.76rem;font-weight:800}.dbgb{padding:14px;font-family:'JetBrains Mono',monospace;font-size:.78rem;line-height:1.58;white-space:pre-wrap;color:#abd0ff}.draft{color:var(--warn);border-bottom:1px dashed var(--line);padding-bottom:12px;margin-bottom:12px}.planbox{margin-bottom:12px;padding:12px;border:1px solid var(--line);border-radius:12px;background:rgba(19,33,63,.72);color:var(--text)}.planhead{font-weight:800;color:var(--strong);margin-bottom:6px}.planmeta{font-size:.75rem;color:var(--muted);margin-bottom:10px}.planitem{padding:10px 0;border-top:1px dashed rgba(255,255,255,.08)}.planitem:first-of-type{border-top:none;padding-top:0}.planname{font-weight:700;color:var(--strong);margin-bottom:4px}.plandetail{color:var(--text);white-space:pre-wrap}.planday{font-size:.76rem;color:var(--muted);margin-bottom:4px}
.loader{display:none;padding:0 18px 8px;color:var(--muted);font-size:.88rem}.bar{padding:14px 18px 18px;border-top:1px solid rgba(255,255,255,.05)}.form{display:grid;grid-template-columns:1fr 120px;gap:12px}
@media (max-width:1600px){.work{grid-template-columns:260px minmax(0,1fr)}.examples{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:1280px){body{overflow:auto}.page{height:auto;grid-template-columns:1fr}.work{grid-template-columns:1fr}.grid,.examples,.form{grid-template-columns:1fr}.span3{grid-column:span 1}.chat{min-height:72vh}}
</style></head><body>
<div class="page">
  <div class="left">
    <div class="hero"><h1>AI Hub v2 Debug Workbench</h1><p>왼쪽에서 프로필과 예제 문장을 넓게 수정하고, 오른쪽 고정 채팅 패널에서 길어진 대화도 스크롤로 계속 확인할 수 있습니다.</p></div>
    <div class="work">
      <div class="stack">
        <div class="panel"><div class="ph"><div class="ey">Session</div><h2>Debug Session Control</h2><p>세션 리셋과 기본 테스트 프로필 복원을 여기서 바로 처리합니다.</p></div>
          <div class="pb">
            <div class="field"><label>User ID</label><input type="text" id="userId" value="__DEFAULT_USER_ID__"></div>
            <div class="meta" style="margin-top:14px"><strong>Session ID</strong><code id="sessionIdValue"></code></div>
            <div class="row" style="margin-top:14px"><button class="btn s" id="btnReset" type="button">New Session</button><button class="btn s" id="btnResetDefaults" type="button">Reset Defaults</button></div>
            <div class="hint" style="margin-top:14px">Reset Defaults를 누르면 프로필 입력값이 기본 테스트 값으로 돌아갑니다. 이 페이지는 user_profile_override 기반 테스트 UI라서 WAS 저장값을 직접 바꾸지는 않습니다.</div>
            <div class="meta" style="margin-top:14px"><strong>Default Test Profile</strong><div class="hint">Persona: registry default<br>MBTI: ISTJ<br>Goal: fat_loss<br>Activity: moderate<br>Diet: balanced<br>Body: 72.5kg / 175cm / 25y</div></div>
          </div></div>
      </div>
      <div class="stack">
        <div class="panel"><div class="ph"><div class="ey">Overrides</div><h2>User Profile Overrides</h2><p>수정 가능한 필드를 넓게 배치했고, 기본값이 미리 채워져 있어 바로 테스트할 수 있습니다.</p></div>
          <div class="pb"><div class="grid">
            <div class="field"><label>Selected Persona</label><select id="personaSelect">__PERSONA_OPTIONS__</select></div>
            <div class="field"><label>MBTI</label><select id="mbtiSelect"><option value="">(Default)</option><option value="ESTJ">ESTJ</option><option value="ESTP">ESTP</option><option value="ENTJ">ENTJ</option><option value="ENTP">ENTP</option><option value="ESFJ">ESFJ</option><option value="ESFP">ESFP</option><option value="ENFJ">ENFJ</option><option value="ENFP">ENFP</option><option value="ISTJ">ISTJ</option><option value="ISTP">ISTP</option><option value="INTJ">INTJ</option><option value="INTP">INTP</option><option value="ISFJ">ISFJ</option><option value="ISFP">ISFP</option><option value="INFJ">INFJ</option><option value="INFP">INFP</option></select></div>
            <div class="field"><label>Goal</label><select id="goalSelect"><option value="">(Default)</option><option value="fat_loss">fat_loss</option><option value="muscle_gain">muscle_gain</option><option value="maintenance">maintenance</option><option value="health">health</option></select></div>
            <div class="field"><label>Activity Level</label><select id="activityLevelSelect"><option value="">(Default)</option><option value="low">low</option><option value="moderate">moderate</option><option value="high">high</option></select></div>
            <div class="field"><label>Diet Type</label><select id="dietTypeSelect"><option value="">(Default)</option><option value="balanced">balanced</option><option value="high_protein">high_protein</option><option value="vegetarian">vegetarian</option><option value="vegan">vegan</option><option value="low_carb">low_carb</option></select></div>
            <div class="field"><label>Gender</label><select id="genderSelect"><option value="">(Default)</option><option value="male">male</option><option value="female">female</option></select></div>
            <div class="field"><label>Age</label><input type="number" id="ageInput"></div>
            <div class="field"><label>Weight (kg)</label><input type="number" step="0.1" id="weightInput"></div>
            <div class="field"><label>Height (cm)</label><input type="number" step="0.1" id="heightInput"></div>
            <div class="field span3"><label>Allergies (comma separated)</label><input type="text" id="allergiesInput"></div>
            <div class="field span3"><label>Injury History (comma separated)</label><input type="text" id="injuryInput"></div>
          </div></div></div>
        <div class="panel"><div class="ph"><div class="ey">Examples</div><h2>Feature Test Messages</h2><p>기능별 예제 버튼을 눌러 입력창에 바로 채우고 테스트할 수 있습니다.</p></div><div class="pb"><div class="examples">__EXAMPLE_SECTIONS__</div></div></div>
      </div>
    </div>
  </div>
  <div class="chat-pane">
    <div class="chat">
      <div class="ch"><div><h2>Response Preview</h2><p>이 패널은 오른쪽에 고정되고, 대화가 길어지면 내부에서 스크롤됩니다.</p></div><span class="pill">Debug UI Ready</span></div>
      <div class="history" id="chatHistory"><div class="msg bot"><div class="bubble">오른쪽 채팅 패널에서 응답과 debug state를 계속 확인해보세요.</div></div></div>
      <div class="loader" id="loader">응답을 생성하는 중입니다...</div>
      <div class="bar"><form class="form" id="chatForm"><input type="text" id="msgInput" placeholder="테스트할 문장을 입력하세요..." autocomplete="off" required><button type="submit" class="btn p" id="btnSend">Send</button></form></div>
    </div>
  </div>
</div>
<script>
const DEFAULT_OVERRIDE_VALUES={persona:'__DEFAULT_PERSONA__',mbti:'ISTJ',goal:'fat_loss',activityLevel:'moderate',dietType:'balanced',gender:'male',age:'25',weight:'72.5',height:'175',allergies:'none',injuryHistory:'none'};
function generateUUID(){return'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g,c=>{const r=Math.random()*16|0;const v=c==='x'?r:(r&0x3|0x8);return v.toString(16);});}
let sessionId=generateUUID();
const chatHistory=document.getElementById('chatHistory');const chatForm=document.getElementById('chatForm');const msgInput=document.getElementById('msgInput');const userIdEl=document.getElementById('userId');const loader=document.getElementById('loader');const sessionIdValue=document.getElementById('sessionIdValue');const personaSelect=document.getElementById('personaSelect');const mbtiSelect=document.getElementById('mbtiSelect');const goalSelect=document.getElementById('goalSelect');const activityLevelSelect=document.getElementById('activityLevelSelect');const dietTypeSelect=document.getElementById('dietTypeSelect');const genderSelect=document.getElementById('genderSelect');const ageInput=document.getElementById('ageInput');const weightInput=document.getElementById('weightInput');const heightInput=document.getElementById('heightInput');const allergiesInput=document.getElementById('allergiesInput');const injuryInput=document.getElementById('injuryInput');
function updateSessionDisplay(){sessionIdValue.textContent=sessionId;}
function applyDefaultOverrides(){personaSelect.value=DEFAULT_OVERRIDE_VALUES.persona;mbtiSelect.value=DEFAULT_OVERRIDE_VALUES.mbti;goalSelect.value=DEFAULT_OVERRIDE_VALUES.goal;activityLevelSelect.value=DEFAULT_OVERRIDE_VALUES.activityLevel;dietTypeSelect.value=DEFAULT_OVERRIDE_VALUES.dietType;genderSelect.value=DEFAULT_OVERRIDE_VALUES.gender;ageInput.value=DEFAULT_OVERRIDE_VALUES.age;weightInput.value=DEFAULT_OVERRIDE_VALUES.weight;heightInput.value=DEFAULT_OVERRIDE_VALUES.height;allergiesInput.value=DEFAULT_OVERRIDE_VALUES.allergies;injuryInput.value=DEFAULT_OVERRIDE_VALUES.injuryHistory;}
document.getElementById('btnReset').onclick=()=>{sessionId=generateUUID();updateSessionDisplay();chatHistory.innerHTML+=`<div style="text-align:center;color:var(--muted);font-size:.8rem;margin:6px 0 2px 0;">--- Session Reset [${sessionId}] ---</div>`;};
document.getElementById('btnResetDefaults').onclick=()=>applyDefaultOverrides();
document.querySelectorAll('[data-example-message]').forEach(button=>{button.addEventListener('click',()=>{msgInput.value=button.dataset.exampleMessage||'';msgInput.focus();});});
function escapeHtml(value){return String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('\"','&quot;').replaceAll(\"'\",'&#39;');}
function renderPlanBlock(state){const items=state?.proposed_plan||[];if(!items.length)return '';const typeLabel=state?.proposed_plan_type==='diet'?'식단':'운동';const actionLabel=state?.proposed_plan_action==='update'?'수정안':'생성안';const rows=items.map((item,index)=>{const name=escapeHtml(item?.name||`item ${index+1}`);const day=item?.day?`<div class=\"planday\">${escapeHtml(item.day)}</div>`:'';const detail=item?.detail?`<div class=\"plandetail\">${escapeHtml(item.detail)}</div>`:'';return `<div class=\"planitem\"><div class=\"planname\">${index+1}. ${name}</div>${day}${detail}</div>`;}).join('');return `<div class=\"planbox\"><div class=\"planhead\">[Proposed ${typeLabel} ${actionLabel}]</div><div class=\"planmeta\">type=${escapeHtml(state?.proposed_plan_type||'unknown')} / action=${escapeHtml(state?.proposed_plan_action||'create')} / count=${items.length}</div>${rows}</div>`;}
function appendMessage(text,sender,debug=null){const row=document.createElement('div');row.className=`msg ${sender}`;const bubble=document.createElement('div');bubble.className='bubble';bubble.innerHTML=text.replace(/\\n/g,'<br>');row.appendChild(bubble);if(debug&&sender==='bot'){const planBlock=renderPlanBlock(debug.state);const panel=document.createElement('div');panel.className='dbg';panel.innerHTML=`<div class="dbgh"><span>TRACE DATA</span><span>STATE SNAPSHOT</span></div><div class="dbgb"><div class="draft"><strong>[Draft Preview]</strong><br>${debug.draft||'N/A'}</div>${planBlock}<strong>[Debug State]</strong><br>${JSON.stringify(debug.state,null,2)}</div>`;row.appendChild(panel);}chatHistory.appendChild(row);chatHistory.scrollTop=chatHistory.scrollHeight;}
function parseCsv(value){return value.split(',').map(item=>item.trim()).filter(Boolean).filter(item=>!['none','없음','null','-'].includes(item.toLowerCase()));}
function parseNumber(value,integerOnly=false){if(!value||!value.trim())return null;const parsed=integerOnly?Number.parseInt(value,10):Number.parseFloat(value);return Number.isNaN(parsed)?null:parsed;}
function buildUserProfileOverride(){const override={};if(personaSelect.value&&personaSelect.value!=='default')override.selected_ai_persona=personaSelect.value;if(mbtiSelect.value)override.mbti=mbtiSelect.value;if(goalSelect.value)override.goal=goalSelect.value;if(activityLevelSelect.value)override.activity_level=activityLevelSelect.value;if(dietTypeSelect.value)override.diet_type=dietTypeSelect.value;if(genderSelect.value)override.gender=genderSelect.value;const age=parseNumber(ageInput.value,true);const weight=parseNumber(weightInput.value);const height=parseNumber(heightInput.value);const allergies=parseCsv(allergiesInput.value);const injuryHistory=parseCsv(injuryInput.value);if(age!==null)override.age=age;if(weight!==null)override.weight=weight;if(height!==null)override.height=height;if(allergies.length)override.allergies=allergies;if(injuryHistory.length)override.injury_history=injuryHistory;return override;}
chatForm.onsubmit=async(e)=>{e.preventDefault();const text=msgInput.value.trim();if(!text)return;msgInput.value='';appendMessage(text,'user');loader.style.display='block';const override=buildUserProfileOverride();try{const body={user_id:userIdEl.value,user_message:text,session_id:sessionId,...(Object.keys(override).length?{user_profile_override:override}:{})};const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await res.json();loader.style.display='none';if(res.ok){appendMessage(data.response,'bot',{draft:data.draft_response,state:data.debug_state});}else{appendMessage('Error: '+(data.error?.message||'Unknown'),'bot');}}catch(err){loader.style.display='none';appendMessage('API Error: '+err.message,'bot');}};
updateSessionDisplay();applyDefaultOverrides();
</script></body></html>
"""


def _build_persona_options() -> tuple[str, str]:
    options: list[str] = []
    default_persona_id = "default"
    for persona in list_active_personas():
        persona_id = escape(str(persona["id"]))
        label = escape(str(persona["label"]))
        prompt_file = escape(str(persona["prompt_file"]))
        if bool(persona["is_default"]):
            default_persona_id = str(persona["id"])
        selected = " selected" if bool(persona["is_default"]) else ""
        options.append(
            f'<option value="{persona_id}"{selected}>{label} ({prompt_file})</option>'
        )
    return "\n".join(options), default_persona_id


def _build_example_sections() -> str:
    sections: list[str] = []
    for group_name, examples in EXAMPLES.items():
        buttons: list[str] = []
        for label, message in examples:
            buttons.append(
                f'<button class="eb" type="button" title="{escape(message)}" '
                f'data-example-message="{escape(message)}">{escape(label)}</button>'
            )
        sections.append(
            '<div class="group">'
            f'<div class="gt">{escape(group_name)}</div>'
            f'<div class="gbtns">{"".join(buttons)}</div>'
            '</div>'
        )
    return "\n".join(sections)


@router.get("/debug", response_class=HTMLResponse)
async def get_debug_page():
    persona_options, default_persona_id = _build_persona_options()
    return (
        html_template
        .replace("__DEFAULT_USER_ID__", escape(DEFAULT_USER_ID))
        .replace("__DEFAULT_PERSONA__", escape(default_persona_id))
        .replace("__PERSONA_OPTIONS__", persona_options)
        .replace("__EXAMPLE_SECTIONS__", _build_example_sections())
    )
