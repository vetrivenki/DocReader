const $=id=>document.getElementById(id);
let selected=null,audioUrl=null;
const api=()=>($("api").value||"").replace(/\/$/,"");
$("api").value=localStorage.getItem("docreader_api")||"";
$("saveApi").onclick=()=>{localStorage.setItem("docreader_api",api());setStatus("Backend URL saved.");};
$("file").onchange=e=>pick(e.target.files[0]);
const drop=$("drop");
["dragenter","dragover"].forEach(x=>drop.addEventListener(x,e=>{e.preventDefault();drop.style.borderColor="#5965d8"}));
["dragleave","drop"].forEach(x=>drop.addEventListener(x,e=>{e.preventDefault();drop.style.borderColor=""}));
drop.addEventListener("drop",e=>pick(e.dataTransfer.files[0]));
function pick(f){if(!f)return;selected=f;$("fileInfo").textContent=f.name+" · "+(f.size/1024/1024).toFixed(2)+" MB";$("fileInfo").classList.remove("hidden");$("extract").disabled=false}
function setStatus(msg,error=false){$("status").textContent=msg;$("status").className="status"+(error?" error":"")}
function requireApi(){if(!api()){setStatus("Add your Cloud Run API URL under Backend settings first.",true);$("api").focus();return false}return true}
$("extract").onclick=async()=>{if(!selected||!requireApi())return;setStatus("Reading document…");$("extract").disabled=true;try{const fd=new FormData();fd.append("file",selected);const r=await fetch(api()+"/extract",{method:"POST",body:fd});const data=await r.json();if(!r.ok)throw new Error(data.detail||"Extraction failed");$("text").value=data.text;$("count").textContent=data.characters.toLocaleString()+" characters";$("editorCard").classList.remove("hidden");setStatus("Document ready.");$("editorCard").scrollIntoView({behavior:"smooth"})}catch(e){setStatus(e.message,true)}finally{$("extract").disabled=false}};
$("text").oninput=()=>$("count").textContent=$("text").value.length.toLocaleString()+" characters";
$("generate").onclick=async()=>{if(!requireApi())return;const text=$("text").value.trim();if(!text)return;const btn=$("generate");btn.disabled=true;btn.textContent="Generating audio…";setStatus("Creating narration. Long documents can take a little while…");try{const r=await fetch(api()+"/speech",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,voice:$("voice").value,instructions:$("style").value})});if(!r.ok){let m="Speech generation failed";try{m=(await r.json()).detail||m}catch{}throw new Error(m)}const blob=await r.blob();if(audioUrl)URL.revokeObjectURL(audioUrl);audioUrl=URL.createObjectURL(blob);$("audio").src=audioUrl;$("download").href=audioUrl;$("audioCard").classList.remove("hidden");setStatus("Audio ready.");$("audioCard").scrollIntoView({behavior:"smooth"})}catch(e){setStatus(e.message,true)}finally{btn.disabled=false;btn.textContent="Generate MP3"}};