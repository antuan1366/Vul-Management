(() => {
    const $ = (id) => document.getElementById(id);
    let rows = [];
    let active = null;
    const selected = new Set();

    function esc(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
    function dt(v) { if (!v) return "—"; const d = new Date(v); return Number.isNaN(d.getTime()) ? "—" : d.toLocaleString(); }
    function human(v) { return String(v || "unknown").replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase()); }
    async function req(url, options) { return apiRequest(url, options); }
    function nvdLabel(item) {
        if (item.nvd_status === "not_found") return "No NVD Detected";
        if (item.nvd_status === "success") return "Found";
        if (item.nvd_status === "partial") return "Partial data";
        if (item.nvd_status === "error") return "Lookup error";
        return "Not checked";
    }
    function render() {
        $("result-count").textContent = rows.length + " Results";
        const body = $("results-table-body");
        if (!rows.length) {
            body.innerHTML = '<tr><td colspan="9">No scan results found. Start a scan from Vulnerabilities → Scan.</td></tr>';
            $("select-all-results").checked = false;
            return;
        }
        body.innerHTML = rows.map((x,i) => {
            const closed = ["approved","rejected"].includes(x.review_status);
            const nvd = nvdLabel(x);
            const actionButtons = '<div class="review-actions">'+
                '<button class="secondary-button small-button" data-action="details" data-id="'+x.id+'">Details</button>'+
                '<button class="secondary-button small-button" data-action="nvd" data-id="'+x.id+'">NVD Lookup</button>'+
                (x.review_status !== "approved" && x.review_status !== "rejected" ? '<button class="primary-button small-button" data-action="accept" data-id="'+x.id+'">Accept</button>' : '')+
                (!closed ? '<button class="danger-button small-button" data-action="reject" data-id="'+x.id+'">Reject</button>' : '')+
                '</div>';
            return '<tr><td><input type="checkbox" class="result-select" data-id="'+x.id+'" '+(selected.has(x.id)?"checked":"")+' '+(x.review_status==="approved"?"disabled":"")+' aria-label="Select '+esc(x.cve_id)+'"></td>'+
                '<td>'+(i+1)+'</td><td><strong>'+esc(x.cve_id)+'</strong></td>'+
                '<td><span title="'+esc(x.message_text)+'">'+esc(x.message_summary || x.message_text || "")+'</span></td>'+
                '<td>'+esc(dt(x.date))+'</td><td>'+esc(x.channel_name)+'<br><span class="review-message">@'+esc(x.channel_username)+'</span></td>'+
                '<td>'+esc(human(x.review_status))+'</td><td><span title="'+esc(x.nvd_error||"")+'">'+esc(nvd)+'</span></td><td>'+actionButtons+'</td></tr>';
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
        $("result-modal-subtitle").textContent = "Collected "+dt(x.date)+" · @"+(x.channel_username||"Telegram");
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
        $("result-nvd-message").textContent = x.nvd_status === "not_found" ? "No NVD Detected" : (x.nvd_missing_fields ? "NVD missing fields: "+x.nvd_missing_fields : "NVD status: "+nvdLabel(x));
        $("result-modal-error").textContent = x.nvd_error || "";
        $("accept-result-button").hidden = x.review_status === "approved";
        $("reject-result-button").hidden = ["approved","rejected"].includes(x.review_status);
        $("result-modal").classList.add("open");
        $("result-modal").setAttribute("aria-hidden","false");
    }
    function closeModal() { $("result-modal").classList.remove("open"); $("result-modal").setAttribute("aria-hidden","true"); active=null; }
    async function openDetails(id) { fillModal(await req("/api/threat-intelligence/scan-results/"+id)); }
    async function lookupNvd(id, openAfter=true) {
        try {
            const result = await req("/api/threat-intelligence/scan-results/"+id+"/enrich",{method:"POST"});
            await loadResults();
            showMessage("NVD data retrieved for "+result.cve_id+".");
            if (openAfter) fillModal(result);
            return result;
        } catch (error) {
            await loadResults();
            const item = rows.find(x=>x.id===id);
            if (item && item.nvd_status === "not_found") {
                showMessage(item.cve_id+": No NVD Detected.",true);
                if (openAfter) fillModal(item);
                return null;
            }
            showMessage(error.message || String(error),true);
            if (openAfter && item) { fillModal(item); $("result-modal-error").textContent=error.message || String(error); }
            throw error;
        }
    }
    function payloadFromModal() {
        return {
            severity:$("result-severity").value||null,
            cvss_score:$("result-cvss").value===""?null:Number($("result-cvss").value),
            affected_product:$("result-product").value||null,
            affected_versions:$("result-versions").value||null,
            remediation:$("result-remediation").value||null,
            mitigation:$("result-mitigation").value||null,
            description:$("result-description").value||null,
            references_text:$("result-references").value||null
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
        const ids=selectedIds().filter(id => { const x=rows.find(r=>r.id===id); return x && !["approved","rejected"].includes(x.review_status); });
        if (!ids.length) return showMessage("Select at least one new or under-review result first.",true);
        if (!window.confirm("Accept "+ids.length+" selected result(s) and add them to Vulnerabilities?")) return;
        let ok=0, failed=0;
        for(const id of ids){try{await req("/api/threat-intelligence/scan-results/"+id+"/approve",{method:"POST"});selected.delete(id);ok++;}catch(e){failed++;}}
        await loadResults(); showMessage("Accepted: "+ok+". Failed: "+failed+".",failed>0);
    }
    async function bulkNvd(ids) {
        ids=ids.filter(id => { const x=rows.find(r=>r.id===id); return x && x.review_status!=="rejected"; });
        if (!ids.length) return showMessage("Select at least one result that has not been rejected.",true);
        let found=0, missing=0, failed=0;
        for(const id of ids){
            try{const x=await req("/api/threat-intelligence/scan-results/"+id+"/enrich",{method:"POST"});if(x.nvd_status==="not_found")missing++;else found++;}
            catch(e){try{const x=await req("/api/threat-intelligence/scan-results/"+id);if(x.nvd_status==="not_found")missing++;else failed++;}catch(_){failed++;}}
        }
        await loadResults();
        showMessage("NVD lookup finished. Data found/updated: "+found+". No NVD Detected: "+missing+". Errors: "+failed+".",failed>0);
    }
    async function bulkDelete() {
        const ids=selectedIds();
        if (!ids.length) return showMessage("Select at least one result first.",true);
        if (!window.confirm("Delete "+ids.length+" selected result(s)? Approved results cannot be deleted here.")) return;
        let ok=0, failed=0;
        for(const id of ids){try{await req("/api/threat-intelligence/scan-results/"+id,{method:"DELETE"});selected.delete(id);ok++;}catch(e){failed++;}}
        await loadResults();showMessage("Deleted: "+ok+". Failed or protected: "+failed+".",failed>0);
    }
    async function handleRowAction(action,id) {
        if(action==="details") return openDetails(id);
        if(action==="nvd") return lookupNvd(id,true);
        if(action==="accept") return accept(id);
        if(action==="reject") return reject(id);
    }
    function init() {
        $("refresh-results-button").addEventListener("click",()=>loadResults().catch(e=>showMessage(e.message,true)));
        $("result-status").addEventListener("change",()=>loadResults().catch(e=>showMessage(e.message,true)));
        $("result-search").addEventListener("input",()=>loadResults().catch(e=>showMessage(e.message,true)));
        $("results-table-body").addEventListener("click",e=>{const b=e.target.closest("[data-action]");if(b)handleRowAction(b.dataset.action,Number(b.dataset.id)).catch(err=>showMessage(err.message,true));});
        $("results-table-body").addEventListener("change",e=>{const cb=e.target.closest(".result-select");if(!cb)return;const id=Number(cb.dataset.id);if(cb.checked)selected.add(id);else selected.delete(id);render();});
        $("select-all-results").addEventListener("change",e=>{for(const x of rows){if(x.review_status==="approved")continue;if(e.target.checked)selected.add(x.id);else selected.delete(x.id);}render();});
        $("bulk-accept-button").addEventListener("click",()=>bulkAccept().catch(e=>showMessage(e.message,true)));
        $("bulk-nvd-button").addEventListener("click",()=>bulkNvd(selectedIds()).catch(e=>showMessage(e.message,true)));
        $("nvd-all-button").addEventListener("click",async()=>{try{const data=await req("/api/threat-intelligence/scan-results?status=all&limit=500");await bulkNvd((data.items||[]).filter(x=>x.review_status!=="rejected").map(x=>x.id));}catch(e){showMessage(e.message,true);}});
        $("bulk-delete-button").addEventListener("click",()=>bulkDelete().catch(e=>showMessage(e.message,true)));
        $("close-result-modal").addEventListener("click",closeModal);
        $("result-modal").addEventListener("click",e=>{if(e.target===$("result-modal"))closeModal();});
        $("save-result-details").addEventListener("click",()=>saveDetails().catch(e=>$("result-modal-error").textContent=e.message));
        $("fetch-result-nvd").addEventListener("click",()=>{if(active)lookupNvd(active.id,true).catch(()=>{});});
        $("accept-result-button").addEventListener("click",()=>{if(active)accept(active.id).catch(e=>$("result-modal-error").textContent=e.message);});
        $("reject-result-button").addEventListener("click",()=>{if(active)reject(active.id).catch(e=>$("result-modal-error").textContent=e.message);});
        loadResults().catch(e=>showMessage(e.message,true));
    }
    document.addEventListener("DOMContentLoaded",init,{once:true});
})();