(() => {
    const $ = (id) => document.getElementById(id);
    let rows = [];
    let active = null;
    const selected = new Set();
    let refreshTimer = null;

    function esc(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
    function dt(v) { if (!v) return "—"; const d = new Date(v); return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString(); }
    function human(v) { return String(v || "unknown").replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase()); }
    async function req(url, options) { return apiRequest(url, options); }
    function nvdLabel(item) {
        if (item.nvd_status === "success") return "Complete";
        if (item.nvd_status === "partial") return "Partial";
        if (item.nvd_status === "not_found") return "No NVD Detected";
        if (item.nvd_status === "error") return "Lookup error";
        if (item.nvd_status === "queued") return "Queued";
        if (item.nvd_status === "skipped") return "Skipped";
        return "Waiting";
    }
    function shortValue(value, fallback) {
        const text = String(value || "").trim();
        return text ? text.replace(/\s+/g, " ").slice(0, 90) : fallback;
    }
    function statusOptions(status) {
        return [
            ["new","New"],["under_review","Under Review"],["approved","Accepted"],["rejected","Rejected"]
        ].map(([value,label]) => '<option value="'+value+'" '+(status===value?"selected":"")+'>'+label+'</option>').join("");
    }
    function render() {
        $("result-count").textContent = rows.length + " Results";
        const body = $("results-table-body");
        if (!rows.length) {
            body.innerHTML = '<tr><td colspan="12">No scan results found. Start a scan from Vulnerabilities → Scan.</td></tr>';
            $("select-all-results").checked = false;
            return;
        }
        body.innerHTML = rows.map((x,i) => {
            const closed = ["approved","rejected"].includes(x.review_status);
            const nvd = nvdLabel(x);
            const actions = '<div class="review-actions">'+
                '<button class="secondary-button small-button" data-action="details" data-id="'+x.id+'">Details</button>'+
                (x.review_status !== "approved" ? '<button class="primary-button small-button" data-action="accept" data-id="'+x.id+'">Accept</button>' : '')+
                '</div>';
            return '<tr>'+
                '<td><input type="checkbox" class="result-select" data-id="'+x.id+'" '+(selected.has(x.id)?"checked":"")+' '+(x.review_status==="approved"?"disabled":"")+' aria-label="Select '+esc(x.cve_id)+'"></td>'+
                '<td>'+(i+1)+'</td>'+
                '<td title="'+esc(dt(x.date))+'">'+esc(dt(x.date))+'</td>'+
                '<td><strong>'+esc(x.cve_id)+'</strong></td>'+
                '<td>'+esc(x.severity || "Data not found in NVD")+'</td>'+
                '<td>'+esc(x.cvss_score ?? "—")+'</td>'+
                '<td class="result-cell" title="'+esc(x.affected_product || "Data not found in NVD")+'">'+esc(shortValue(x.affected_product,"Data not found in NVD"))+'</td>'+
                '<td class="result-cell" title="'+esc(x.affected_versions || "Data not found in NVD")+'">'+esc(shortValue(x.affected_versions,"Data not found in NVD"))+'</td>'+
                '<td class="result-cell" title="'+esc(x.remediation || "NVD does not provide a dedicated remediation field for every CVE.")+'">'+esc(shortValue(x.remediation,"Not available"))+'</td>'+
                '<td><select class="review-status-select" data-action="status" data-id="'+x.id+'" aria-label="Change status for '+esc(x.cve_id)+'" '+(x.review_status==="approved"?"disabled":"")+'>'+statusOptions(x.review_status)+'</select></td>'+
                '<td><span title="'+esc(x.nvd_error || x.nvd_missing_fields || "")+'">'+esc(nvd)+'</span></td>'+
                '<td>'+actions+'</td></tr>';
        }).join("");
        const selectable = rows.filter(x=>x.review_status!=="approved");
        $("select-all-results").checked = selectable.length > 0 && selectable.every(x=>selected.has(x.id));
    }
    async function loadResults() {
        const query = new URLSearchParams({status:$("result-status").value,q:$("result-search").value.trim(),limit:"500"});
        const data = await req("/api/threat-intelligence/scan-results?"+query.toString());
        rows = data.items || [];
        const visibleIds = new Set(rows.map(x=>x.id));
        for (const id of selected) if (!visibleIds.has(id)) selected.delete(id);
        render();
    }
    function showMessage(message, isError=false) {
        $("bulk-message").textContent = message || "";
        $("bulk-message").classList.toggle("error",Boolean(isError));
    }
    function fillModal(x) {
        active = x;
        $("result-modal-title").textContent = x.cve_id;
        $("result-modal-subtitle").textContent = "Collected "+dt(x.date)+" · @"+(x.channel_username||"Telegram")+" · Status: "+human(x.review_status);
        $("result-original-message").textContent = x.message_text || "No original message text is available.";
        $("result-message-link").hidden = !x.message_url;
        $("result-message-link").href = x.message_url || "#";
        $("result-severity").value = x.severity || "";
        $("result-cvss").value = x.cvss_score ?? "";
        $("result-product").value = x.affected_product || "";
        $("result-versions").value = x.affected_versions || "";
        $("result-remediation").value = x.remediation || "";
        $("result-mitigation").value = x.mitigation || "";
        $("result-description").value = x.nvd_description || "";
        $("result-references").value = x.references_text || "";
        $("result-nvd-message").textContent = x.nvd_status === "not_found"
            ? "No NVD Detected"
            : (x.nvd_missing_fields ? "NVD missing fields: "+x.nvd_missing_fields : "NVD status: "+nvdLabel(x));
        $("result-modal-error").textContent = x.nvd_error || "";
        $("accept-result-button").hidden = x.review_status === "approved";
        $("reject-result-button").hidden = ["approved","rejected"].includes(x.review_status);
        $("result-modal").classList.add("open");
        $("result-modal").setAttribute("aria-hidden","false");
    }
    function closeModal() { $("result-modal").classList.remove("open"); $("result-modal").setAttribute("aria-hidden","true"); active=null; }
    async function openDetails(id) { fillModal(await req("/api/threat-intelligence/scan-results/"+id)); }
    function payloadFromModal() {
        return {
            severity:$("result-severity").value.trim()||null,
            cvss_score:$("result-cvss").value===""?null:Number($("result-cvss").value),
            affected_product:$("result-product").value.trim()||null,
            affected_versions:$("result-versions").value.trim()||null,
            remediation:$("result-remediation").value.trim()||null,
            mitigation:$("result-mitigation").value.trim()||null,
            description:$("result-description").value.trim()||null,
            references_text:$("result-references").value.trim()||null
        };
    }
    async function saveDetails() {
        if (!active) return;
        active = await req("/api/threat-intelligence/scan-results/"+active.id,{method:"PUT",body:JSON.stringify(payloadFromModal())});
        fillModal(active);
        await loadResults();
        showMessage("Details saved.");
    }
    async function accept(id) {
        if (!window.confirm("Accept this CVE and add it to Vulnerabilities?")) return;
        if (active && active.id===id) await req("/api/threat-intelligence/scan-results/"+id,{method:"PUT",body:JSON.stringify(payloadFromModal())});
        await req("/api/threat-intelligence/scan-results/"+id+"/approve",{method:"POST"});
        selected.delete(id);
        if (active && active.id===id) closeModal();
        await loadResults();
        showMessage("Accepted CVE and added it to Vulnerabilities.");
    }
    async function changeStatus(id, status) {
        const record = rows.find(x=>x.id===id);
        if (!record || record.review_status===status) return;
        try {
            if (status === "approved") {
                if (!window.confirm("Accept "+record.cve_id+" and add it to Vulnerabilities?")) {
                    await loadResults();
                    return;
                }
                await req("/api/threat-intelligence/scan-results/"+id+"/approve",{method:"POST"});
                selected.delete(id);
                showMessage(record.cve_id+" accepted and added to Vulnerabilities.");
            } else {
                await req("/api/threat-intelligence/scan-results/"+id+"/review",{
                    method:"POST",body:JSON.stringify({status})
                });
                showMessage(record.cve_id+" status changed to "+human(status)+".");
            }
            await loadResults();
            if (active && active.id===id) {
                active = await req("/api/threat-intelligence/scan-results/"+id);
                fillModal(active);
            }
        } catch (error) {
            showMessage(error.message || String(error),true);
            await loadResults();
        }
    }
    async function reject(id) {
        if (!window.confirm("Reject this CVE?")) return;
        await req("/api/threat-intelligence/scan-results/"+id+"/review",{method:"POST",body:JSON.stringify({status:"rejected"})});
        selected.delete(id);
        if (active && active.id===id) closeModal();
        await loadResults();
        showMessage("CVE rejected.");
    }
    function selectedIds() { return Array.from(selected); }
    async function bulkAccept() {
        const ids=selectedIds().filter(id => { const x=rows.find(r=>r.id===id); return x && x.review_status!=="approved"; });
        if (!ids.length) return showMessage("Select at least one result first.",true);
        if (!window.confirm("Accept "+ids.length+" selected result(s) and add them to Vulnerabilities?")) return;
        let ok=0, failed=0;
        for(const id of ids){try{await req("/api/threat-intelligence/scan-results/"+id+"/approve",{method:"POST"});selected.delete(id);ok++;}catch(e){failed++;}}
        await loadResults(); showMessage("Accepted: "+ok+". Failed: "+failed+".",failed>0);
    }
    async function bulkDelete() {
        const ids=selectedIds();
        if (!ids.length) return showMessage("Select at least one result first.",true);
        if (!window.confirm("Delete "+ids.length+" selected result(s)? Accepted results cannot be deleted here.")) return;
        let ok=0, failed=0;
        for(const id of ids){try{await req("/api/threat-intelligence/scan-results/"+id,{method:"DELETE"});selected.delete(id);ok++;}catch(e){failed++;}}
        await loadResults();showMessage("Deleted: "+ok+". Failed or protected: "+failed+".",failed>0);
    }
    async function handleRowAction(action,id) {
        if(action==="details") return openDetails(id);
        if(action==="accept") return accept(id);
    }
    function init() {
        $("refresh-results-button").addEventListener("click",()=>loadResults().catch(e=>showMessage(e.message,true)));
        $("result-status").addEventListener("change",()=>loadResults().catch(e=>showMessage(e.message,true)));
        $("result-search").addEventListener("input",()=>loadResults().catch(e=>showMessage(e.message,true)));
        $("results-table-body").addEventListener("click",e=>{const b=e.target.closest("button[data-action]");if(b)handleRowAction(b.dataset.action,Number(b.dataset.id)).catch(err=>showMessage(err.message,true));});
        $("results-table-body").addEventListener("change",e=>{
            const cb=e.target.closest(".result-select");
            if(cb){const id=Number(cb.dataset.id);if(cb.checked)selected.add(id);else selected.delete(id);render();return;}
            const status=e.target.closest('select[data-action="status"]');
            if(status)changeStatus(Number(status.dataset.id),status.value);
        });
        $("select-all-results").addEventListener("change",e=>{for(const x of rows){if(x.review_status==="approved")continue;if(e.target.checked)selected.add(x.id);else selected.delete(x.id);}render();});
        $("bulk-accept-button").addEventListener("click",()=>bulkAccept().catch(e=>showMessage(e.message,true)));
        $("bulk-delete-button").addEventListener("click",()=>bulkDelete().catch(e=>showMessage(e.message,true)));
        $("close-result-modal").addEventListener("click",closeModal);
        $("result-modal").addEventListener("click",e=>{if(e.target===$("result-modal"))closeModal();});
        $("save-result-details").addEventListener("click",()=>saveDetails().catch(e=>$("result-modal-error").textContent=e.message));
        $("accept-result-button").addEventListener("click",()=>{if(active)accept(active.id).catch(e=>$("result-modal-error").textContent=e.message);});
        $("reject-result-button").addEventListener("click",()=>{if(active)reject(active.id).catch(e=>$("result-modal-error").textContent=e.message);});
        loadResults().catch(e=>showMessage(e.message,true));
        refreshTimer = window.setInterval(()=>{
            if(document.activeElement && document.activeElement.closest("#results-table-body")) return;
            loadResults().catch(e=>showMessage(e.message,true));
        },5000);
    }
    document.addEventListener("DOMContentLoaded",init,{once:true});
})();