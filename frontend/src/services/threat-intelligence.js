(() => {
    const $ = (id) => document.getElementById(id);
    let activeDetail = null;
    let detailMode = "scan";
    function esc(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
    function dt(v) { if (!v) return "—"; const d = new Date(v); return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString(); }
    function label(v) { return String(v || "unknown").replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase()); }
    function btn(text, action, id, cls) { return '<button type="button" class="' + (cls || "secondary-button") + '" data-action="' + action + '" data-id="' + id + '">' + text + '</button>'; }
    async function req(url, options) { return apiRequest(url, options); }
    async function loadResults() {
        const s = $("ti-status-filter").value, q = $("ti-search-results").value.trim();
        const data = await req("/api/threat-intelligence/scan-results?status=" + encodeURIComponent(s) + "&q=" + encodeURIComponent(q) + "&limit=500");
        $("ti-scan-count").textContent = data.total + " Results";
        $("ti-results-body").innerHTML = data.items.map((x, i) => '<tr><td>'+(i+1)+'</td><td><strong>'+esc(x.cve_id)+'</strong></td><td><span class="ti-message" title="'+esc(x.message_text)+'">'+esc(x.message_summary)+'</span></td><td>'+esc(dt(x.date))+'</td><td>'+esc(x.channel_name)+'<br><span class="ti-muted">@'+esc(x.channel_username)+'</span></td><td>'+esc(label(x.review_status))+'</td><td>'+esc(label(x.nvd_status))+(x.nvd_error?'<div class="ti-error">'+esc(x.nvd_error)+'</div>':"")+'</td><td><div class="ti-actions">'+btn("Review","review",x.id)+(x.review_status!=="rejected"&&x.review_status!=="approved"?btn("NVD Lookup","enrich",x.id)+btn("Details","details",x.id)+btn("Reject","reject",x.id):"")+'</div></td></tr>').join("") || '<tr><td colspan="8">No scan results yet. Add Telegram feeds and start a scan.</td></tr>';
    }
    async function loadIntelligence() {
        const q = $("ti-search-intelligence").value.trim();
        const data = await req("/api/threat-intelligence/intelligence?q="+encodeURIComponent(q)+"&limit=500");
        $("ti-intelligence-count").textContent = data.total + " CVEs";
        $("ti-intelligence-body").innerHTML = data.items.map((x,i)=>'<tr><td>'+(i+1)+'</td><td><strong>'+esc(x.cve_id)+'</strong></td><td>'+esc(x.severity||"Data not found in NVD")+(x.cvss_score!=null?'<br><span class="ti-muted">CVSS '+esc(x.cvss_score)+'</span>':"")+'</td><td><span class="ti-message" title="'+esc(x.affected_product||"Data not found in NVD")+'">'+esc(x.affected_product||"Data not found in NVD")+'</span></td><td>'+esc(dt(x.date))+'</td><td>'+(x.jira_issue_url?'<a href="'+esc(x.jira_issue_url)+'" target="_blank" rel="noopener">'+esc(x.jira_issue_key||"Open Jira")+'</a>':esc(label(x.jira_status)))+'</td><td><div class="ti-actions">'+btn("Edit","edit-intelligence",x.id)+(x.jira_issue_key?"":btn("Send Jira Ticket","jira",x.id,"primary-button"))+'</div></td></tr>').join("")||'<tr><td colspan="7">No CVEs have been approved into Intelligence.</td></tr>';
    }
    async function loadRuns() {
        const data = await req("/api/threat-intelligence/scan-runs?limit=200");
        $("ti-runs-count").textContent=data.total+" Runs";
        $("ti-runs-body").innerHTML=data.items.map((x,i)=>'<tr><td>'+(i+1)+'</td><td>'+(x.mode==="from_date"?"From date":"New messages")+'</td><td>'+esc(dt(x.date))+'</td><td>'+esc(label(x.status))+'</td><td>'+x.channels_processed+'/'+x.channels_total+'</td><td>'+x.messages_processed+'</td><td>'+x.cve_occurrences+'</td><td class="ti-error">'+esc(x.error_message||"—")+'</td></tr>').join("")||'<tr><td colspan="8">No scans have run yet.</td></tr>';
    }
    async function loadFeeds() {
        const data=await req("/api/threat-intelligence/feeds");
        $("ti-feeds-count").textContent=data.total+" Channels"; window.__tiFeeds=data.items;
        $("ti-feeds-body").innerHTML=data.items.map((x,i)=>'<tr><td>'+(i+1)+'</td><td>'+esc(x.name)+'</td><td><a href="https://t.me/'+encodeURIComponent(x.channel_username)+'" target="_blank" rel="noopener">@'+esc(x.channel_username)+'</a></td><td>'+(x.enabled?"Enabled":"Disabled")+'</td><td>'+(x.last_message_id??"—")+'</td><td><div class="ti-actions">'+btn(x.enabled?"Disable":"Enable","toggle-feed",x.id)+btn("Delete","delete-feed",x.id)+'</div></td></tr>').join("")||'<tr><td colspan="6">No Telegram channels configured.</td></tr>';
    }
    async function loadSchedule(){
        const x=await req("/api/threat-intelligence/schedule");
        $("ti-schedule-enabled").checked=Boolean(x.enabled);
        $("ti-schedule-frequency").value=x.frequency||"daily";
        $("ti-schedule-time").value=x.scan_time||"02:00";
        $("ti-schedule-day").value=String(x.day_of_week??0);
        $("ti-schedule-status").textContent=x.last_run_date?"Last scheduled run: "+dt(x.last_run_date):"No scheduled run yet";
        $("ti-schedule-day").disabled=x.frequency!=="weekly";
    }
    async function refreshAll(){ await Promise.all([loadResults(),loadIntelligence(),loadRuns(),loadFeeds(),loadSchedule()]); }
    function openModal(x, mode) {
        activeDetail=x; detailMode=mode;
        $("ti-modal-title").textContent=x.cve_id||"CVE Details";
        $("ti-modal-subtitle").textContent=mode==="intelligence"?"Edit approved Intelligence record":"From @"+(x.channel_username||"Telegram")+" · DATE "+dt(x.date);
        $("ti-modal-message").textContent=x.message_text||x.source_message||x.description||"";
        $("ti-severity").value=x.severity||""; $("ti-cvss").value=x.cvss_score??"";
        $("ti-product").value=x.affected_product||""; $("ti-versions").value=x.affected_versions||"";
        $("ti-remediation").value=x.remediation||""; $("ti-mitigation").value=x.mitigation||"";
        $("ti-description").value=x.nvd_description||x.description||""; $("ti-references").value=x.references_text||"";
        $("ti-nvd-note").textContent=x.nvd_missing_fields?"NVD fields unavailable: "+x.nvd_missing_fields:(x.nvd_status?"NVD status: "+label(x.nvd_status):"");
        $("ti-detail-error").textContent=x.nvd_error||"";
        $("ti-approve-result").hidden=mode!=="scan"||x.review_status==="approved"||x.review_status==="rejected";
        $("ti-enrich-again").hidden=mode!=="scan"||x.review_status==="rejected";
        $("ti-send-jira").hidden=mode!=="intelligence"||Boolean(x.jira_issue_key);
        $("ti-modal").classList.add("open"); $("ti-modal").setAttribute("aria-hidden","false");
    }
    function closeModal(){ $("ti-modal").classList.remove("open"); $("ti-modal").setAttribute("aria-hidden","true"); activeDetail=null; }
    async function openScan(id, enrich) {
        let x=await req("/api/threat-intelligence/scan-results/"+id);
        if(enrich){x=await req("/api/threat-intelligence/scan-results/"+id+"/enrich",{method:"POST"});await loadResults();}
        openModal(x,"scan");
    }
    async function saveDetails() {
        if(!activeDetail)return;
        const payload={severity:$("ti-severity").value||null,cvss_score:$("ti-cvss").value===""?null:Number($("ti-cvss").value),affected_product:$("ti-product").value||null,affected_versions:$("ti-versions").value||null,remediation:$("ti-remediation").value||null,mitigation:$("ti-mitigation").value||null,description:$("ti-description").value||null,references_text:$("ti-references").value||null};
        const url=detailMode==="scan"?"/api/threat-intelligence/scan-results/"+activeDetail.id:"/api/threat-intelligence/intelligence/"+activeDetail.id;
        const x=await req(url,{method:"PUT",body:JSON.stringify(payload)});
        openModal(x,detailMode);
        if(detailMode==="scan")await loadResults();else await loadIntelligence();
    }
    async function approveCurrent(){
        if(!activeDetail)return;
        const id=activeDetail.id;
        await saveDetails();
        await req("/api/threat-intelligence/scan-results/"+id+"/approve",{method:"POST"});
        closeModal(); await Promise.all([loadResults(),loadIntelligence()]);
    }
    async function startScan(mode){
        const payload={mode};
        if(mode==="from_date"){
            const value=window.prompt("Enter start date/time (YYYY-MM-DDTHH:mm), for example 2026-01-01T00:00");
            if(!value)return;
            if(Number.isNaN(new Date(value).getTime())){window.alert("The date/time format is invalid.");return;}
            payload.start_date=new Date(value).toISOString();
        }
        const result=await req("/api/threat-intelligence/scan",{method:"POST",body:JSON.stringify(payload)});
        window.alert("Telegram scan #"+result.scan_run_id+" started. Follow progress in Scan History.");
        await loadRuns();
    }
    async function action(name,id){
        if(name==="details")return openScan(id,false);
        if(name==="enrich")return openScan(id,true);
        if(name==="review"){await req("/api/threat-intelligence/scan-results/"+id+"/review",{method:"POST",body:JSON.stringify({status:"under_review"})});await loadResults();return openScan(id,false);}
        if(name==="reject"){if(!window.confirm("Reject this scan result?"))return;await req("/api/threat-intelligence/scan-results/"+id+"/review",{method:"POST",body:JSON.stringify({status:"rejected"})});return loadResults();}
        if(name==="edit-intelligence")return openModal(await req("/api/threat-intelligence/intelligence/"+id),"intelligence");
        if(name==="jira"){const r=await req("/api/threat-intelligence/intelligence/"+id+"/jira",{method:"POST"});window.alert("Jira issue: "+r.issue_key+"\n"+r.issue_url);return loadIntelligence();}
        if(name==="toggle-feed"){const f=(window.__tiFeeds||[]).find(x=>x.id===Number(id));if(!f)return;await req("/api/threat-intelligence/feeds/"+id,{method:"PUT",body:JSON.stringify({enabled:!f.enabled})});return loadFeeds();}
        if(name==="delete-feed"){if(!window.confirm("Delete this Telegram feed? Existing scan results will be kept."))return;await req("/api/threat-intelligence/feeds/"+id,{method:"DELETE"});return loadFeeds();}
    }
    function error(e){const m=e?.message||String(e);$("ti-detail-error").textContent=m;window.alert(m);}
    document.querySelectorAll(".ti-tab").forEach(t=>t.addEventListener("click",()=>{document.querySelectorAll(".ti-tab").forEach(x=>x.classList.toggle("active",x===t));document.querySelectorAll(".ti-panel").forEach(p=>p.hidden=p.id!=="panel-"+t.dataset.tab);if(t.dataset.tab==="scan-history")loadRuns().catch(error);if(t.dataset.tab==="telegram-feeds")loadFeeds().catch(error);}));
    $("ti-scan-new").addEventListener("click",()=>startScan("new").catch(error)); $("ti-scan-history").addEventListener("click",()=>startScan("from_date").catch(error));
    $("ti-refresh-results").addEventListener("click",()=>loadResults().catch(error)); $("ti-refresh-intelligence").addEventListener("click",()=>loadIntelligence().catch(error));
    $("ti-status-filter").addEventListener("change",()=>loadResults().catch(error)); $("ti-search-results").addEventListener("input",()=>loadResults().catch(error)); $("ti-search-intelligence").addEventListener("input",()=>loadIntelligence().catch(error));
    $("ti-modal-close").addEventListener("click",closeModal); $("ti-modal").addEventListener("click",e=>{if(e.target===$("ti-modal"))closeModal();});
    $("ti-detail-form").addEventListener("submit",async e=>{e.preventDefault();try{await saveDetails();}catch(ex){error(ex);}});
    $("ti-approve-result").addEventListener("click",async()=>{try{await approveCurrent();}catch(ex){error(ex);}});
    $("ti-enrich-again").addEventListener("click",async()=>{if(activeDetail)try{await openScan(activeDetail.id,true);}catch(ex){error(ex);}});
    $("ti-send-jira").addEventListener("click",async()=>{if(!activeDetail)return;try{const r=await req("/api/threat-intelligence/intelligence/"+activeDetail.id+"/jira",{method:"POST"});window.alert("Jira issue: "+r.issue_key+"\n"+r.issue_url);closeModal();await loadIntelligence();}catch(ex){error(ex);}});
    $("ti-results-body").addEventListener("click",e=>{const b=e.target.closest("[data-action]");if(b)action(b.dataset.action,b.dataset.id).catch(error);});
    $("ti-intelligence-body").addEventListener("click",e=>{const b=e.target.closest("[data-action]");if(b)action(b.dataset.action,b.dataset.id).catch(error);});
    $("ti-feeds-body").addEventListener("click",e=>{const b=e.target.closest("[data-action]");if(b)action(b.dataset.action,b.dataset.id).catch(error);});
    $("ti-feed-form").addEventListener("submit",async e=>{e.preventDefault();try{await req("/api/threat-intelligence/feeds",{method:"POST",body:JSON.stringify({name:$("ti-feed-name").value.trim(),channel_username:$("ti-feed-channel").value.trim(),enabled:true})});$("ti-feed-form").reset();await loadFeeds();}catch(ex){error(ex);}});
    $("ti-schedule-frequency").addEventListener("change",()=>{$("ti-schedule-day").disabled=$("ti-schedule-frequency").value!=="weekly";});
    $("ti-schedule-form").addEventListener("submit",async e=>{
        e.preventDefault();
        try{
            const x=await req("/api/threat-intelligence/schedule",{method:"PUT",body:JSON.stringify({enabled:$("ti-schedule-enabled").checked,frequency:$("ti-schedule-frequency").value,scan_time:$("ti-schedule-time").value,day_of_week:Number($("ti-schedule-day").value)})});
            $("ti-schedule-status").textContent="Schedule saved. Last run: "+dt(x.last_run_date);
        }catch(ex){error(ex);}
    });
    refreshAll().catch(error);
})();
