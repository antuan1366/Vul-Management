(() => {
    const $ = (id) => document.getElementById(id);
    let activeId = null;
    let records = [];
    function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
    function dt(v){if(!v)return "—";const d=new Date(v);return Number.isNaN(d.getTime())?"—":d.toLocaleString();}
    async function req(url,options){return apiRequest(url,options);}
    function message(text,error=false){$("vulnerability-message").textContent=text||"";$("vulnerability-message").classList.toggle("error",Boolean(error));}
    async function loadRecords(){
        const q=$("vulnerability-search").value.trim();
        const data=await req("/api/threat-intelligence/intelligence?q="+encodeURIComponent(q)+"&limit=500");
        records=data.items||[];
        const total=data.total??records.length;
        $("vulnerability-count").textContent=total+" "+(total===1?"Vulnerability":"Vulnerabilities");
        $("vulnerabilities-table-body").innerHTML=records.map((x,i)=>'<tr><td>'+(i+1)+'</td><td><strong>'+esc(x.cve_id)+'</strong></td><td>'+esc(x.severity||"Data not found in NVD")+'</td><td>'+esc(x.cvss_score??"—")+'</td><td><span title="'+esc(x.affected_product||"Data not found in NVD")+'">'+esc(x.affected_product||"Data not found in NVD")+'</span></td><td><span title="'+esc(x.affected_versions||"Data not found in NVD")+'">'+esc(x.affected_versions||"Data not found in NVD")+'</span></td><td>'+esc(dt(x.date))+'</td><td>'+(x.jira_issue_url?'<a href="'+esc(x.jira_issue_url)+'" target="_blank" rel="noopener">'+esc(x.jira_issue_key||"Open Jira")+'</a>':esc(x.jira_status||"Not sent"))+'</td><td><div class="vul-actions"><button class="secondary-button small-button" data-action="edit" data-id="'+x.id+'">Edit</button>'+(x.jira_issue_key?"":'<button class="primary-button small-button" data-action="jira" data-id="'+x.id+'">Create Jira</button>')+'<button class="danger-button small-button" data-action="delete" data-id="'+x.id+'">Delete</button>'+'</div></td></tr>').join("")||'<tr><td colspan="9">No vulnerabilities yet. Accept a finding in Scan Result or select Add New.</td></tr>';
    }
    function resetForm(){
        activeId=null;
        $("vulnerability-form").reset();
        $("vul-cve-id").disabled=false;
        $("vulnerability-modal-title").textContent="Add Vulnerability";
        $("vulnerability-modal-description").textContent="Enter the CVE details and available remediation information.";
        $("save-vulnerability-button").textContent="Save Vulnerability";
        $("vulnerability-form-message").textContent="";
    }
    function openModal(record=null){
        resetForm();
        if(record){
            activeId=record.id;
            $("vulnerability-modal-title").textContent="Edit Vulnerability";
            $("vulnerability-modal-description").textContent="Update vulnerability details for "+record.cve_id+".";
            $("save-vulnerability-button").textContent="Save Changes";
            $("vul-cve-id").value=record.cve_id;
            $("vul-cve-id").disabled=true;
            $("vul-severity").value=record.severity||"";
            $("vul-cvss").value=record.cvss_score??"";
            $("vul-product").value=record.affected_product||"";
            $("vul-versions").value=record.affected_versions||"";
            $("vul-remediation").value=record.remediation||"";
            $("vul-mitigation").value=record.mitigation||"";
            $("vul-description").value=record.description||"";
            $("vul-references").value=record.references_text||"";
        }
        $("vulnerability-modal").classList.add("is-open");
        $("vulnerability-modal").setAttribute("aria-hidden","false");
    }
    function closeModal(){$("vulnerability-modal").classList.remove("is-open");$("vulnerability-modal").setAttribute("aria-hidden","true");activeId=null;}
    function formPayload(){
        return {cve_id:$("vul-cve-id").value.trim().toUpperCase(),severity:$("vul-severity").value.trim()||null,cvss_score:$("vul-cvss").value===""?null:Number($("vul-cvss").value),affected_product:$("vul-product").value.trim()||null,affected_versions:$("vul-versions").value.trim()||null,remediation:$("vul-remediation").value.trim()||null,mitigation:$("vul-mitigation").value.trim()||null,description:$("vul-description").value.trim()||null,references_text:$("vul-references").value.trim()||null};
    }
    async function saveRecord(event){
        event.preventDefault();
        const button=$("save-vulnerability-button");
        button.disabled=true;
        $("vulnerability-form-message").textContent="Saving…";
        const payload=formPayload();
        try{
            if(activeId){
                delete payload.cve_id;
                await req("/api/threat-intelligence/intelligence/"+activeId,{method:"PUT",body:JSON.stringify(payload)});
                message("Vulnerability updated.");
            }else{
                await req("/api/threat-intelligence/intelligence",{method:"POST",body:JSON.stringify(payload)});
                message("Vulnerability added.");
            }
            closeModal();
            await loadRecords();
        }catch(error){$("vulnerability-form-message").textContent=error.message||String(error);}
        finally{button.disabled=false;}
    }
    async function handleAction(action,id){
        const record=records.find(x=>x.id===id);
        if(action==="edit")return openModal(record);
        if(action==="jira"){
            if(!window.confirm("Create a Jira issue for "+record.cve_id+"?"))return;
            const result=await req("/api/threat-intelligence/intelligence/"+id+"/jira",{method:"POST"});
            message("Jira issue created: "+result.issue_key);
            await loadRecords();
        }
        if(action==="delete"){
            if(!record)return;
            const warning = record.jira_issue_key
                ? "This vulnerability has Jira issue "+record.jira_issue_key+". Deleting it here will not delete that Jira issue. Continue?"
                : "Delete "+record.cve_id+" from the Vulnerability Register? This cannot be undone.";
            if(!window.confirm(warning))return;
            await req("/api/threat-intelligence/intelligence/"+id,{method:"DELETE"});
            message(record.cve_id+" deleted from the Vulnerability Register.");
            await loadRecords();
        }
    }
    function init(){
        $("add-vulnerability-button").addEventListener("click",()=>openModal());
        $("vulnerability-search").addEventListener("input",()=>loadRecords().catch(e=>message(e.message,true)));
        $("vulnerabilities-table-body").addEventListener("click",e=>{const b=e.target.closest("[data-action]");if(b)handleAction(b.dataset.action,Number(b.dataset.id)).catch(err=>message(err.message,true));});
        $("vulnerability-form").addEventListener("submit",saveRecord);
        $("close-vulnerability-modal").addEventListener("click",closeModal);
        $("cancel-vulnerability-modal").addEventListener("click",closeModal);
        $("vulnerability-modal").addEventListener("click",e=>{if(e.target===$("vulnerability-modal"))closeModal();});
        loadRecords().catch(e=>message(e.message,true));
    }
    document.addEventListener("DOMContentLoaded",init,{once:true});
})();