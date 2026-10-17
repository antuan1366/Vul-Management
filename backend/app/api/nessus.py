import json,re
from datetime import datetime
from xml.etree.ElementTree import ParseError
from defusedxml import ElementTree as ET
from fastapi import APIRouter,Depends,File,HTTPException,UploadFile
from pydantic import BaseModel,Field
from sqlalchemy import select,or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.nessus import NessusImport,NessusFinding,NessusHostMapping
from app.models.threat_intelligence import ThreatIntelligence

router=APIRouter(prefix="/api/nessus",tags=["Nessus"])
MAX_BYTES=25*1024*1024
CVE=re.compile(r"\bCVE-\d{4}-\d{4,}\b",re.I)
SEVERITY={0:"Info",1:"Low",2:"Medium",3:"High",4:"Critical"}
def lname(tag): return tag.rsplit("}",1)[-1].split(":")[-1].lower()
def txt(node,names):
    names={n.lower() for n in names}
    for e in node.iter():
        if e is not node and lname(e.tag) in names and e.text and e.text.strip(): return e.text.strip()
    return None
def direct(node,name):
    for e in list(node):
        if lname(e.tag)==name.lower() and e.text and e.text.strip(): return e.text.strip()
    return None
def props(host):
    out={}
    for e in host.iter():
        if lname(e.tag)=="tag" and e.attrib.get("name") and e.text: out[e.attrib["name"].lower()]=e.text.strip()
    return out
def mapping(db,p,hn):
    candidates={"hostname":p.get("hostname") or hn,"fqdn":p.get("host-fqdn"),"ip":p.get("host-ip"),"mac":p.get("mac-address"),"uuid":p.get("host-uuid")}
    for rule in db.scalars(select(NessusHostMapping).where(NessusHostMapping.enabled.is_(True)).order_by(NessusHostMapping.id)).all():
        val=candidates.get(rule.match_type)
        if val and val.strip().casefold()==rule.reported_value.strip().casefold(): return rule.actual_hostname
    return None
def impdict(x):
    return {k:getattr(x,k) for k in ("id","filename","report_name","status","host_count","finding_count","error_message","uploaded_at","analysed_at")}
def fdict(x):
    d={k:getattr(x,k) for k in ("id","import_id","finding_key","host_name","host_ip","host_fqdn","host_mac","host_uuid","resolved_hostname","plugin_id","plugin_name","plugin_family","severity","cvss_score","protocol","port","service_name","description","synopsis","solution","plugin_output","references_text","exploit_available","first_found","last_found","review_status","review_notes","reviewed_at","created_at")}
    try:d["cve_ids"]=json.loads(x.cve_ids or "[]")
    except ValueError:d["cve_ids"]=[]
    return d
def analyse(db,report):
    if report.status=="analysed": raise ValueError("This report has already been analysed.")
    try: root=ET.fromstring(report.raw_xml)
    except Exception as e: raise ValueError("The uploaded file is not valid, safe XML.") from e
    section=root if lname(root.tag)=="report" else next((x for x in root.iter() if lname(x.tag)=="report"),None)
    if section is None: raise ValueError("No Nessus Report section found. Policy-only exports are unsupported.")
    hosts=[x for x in list(section) if lname(x.tag)=="reporthost"]
    if not hosts: raise ValueError("The report contains no ReportHost scan results.")
    new=[]
    for hi,host in enumerate(hosts):
        hn=host.attrib.get("name") or "Unknown host"; p=props(host)
        for ri,item in enumerate(x for x in list(host) if lname(x.tag)=="reportitem"):
            pid=item.attrib.get("pluginID") or item.attrib.get("pluginId"); pname=item.attrib.get("pluginName") or "Unnamed plugin finding"
            try: sev=SEVERITY.get(int(item.attrib.get("severity","0")),"Info")
            except ValueError: sev=(txt(item,["risk_factor"]) or "Info").title()
            scoretext=txt(item,["cvss4_base_score","cvss3_base_score","cvss_base_score"])
            try: score=float(scoretext) if scoretext else None
            except ValueError: score=None
            cves=sorted({v.upper() for e in item.iter() if lname(e.tag)=="cve" for v in CVE.findall(e.text or "")})
            refs=[e.text.strip() for e in item.iter() if lname(e.tag) in {"see_also","xref"} and e.text and e.text.strip()]
            try: port=int(item.attrib.get("port","0")) or None
            except ValueError: port=None
            new.append(NessusFinding(import_id=report.id,finding_key=f"{hi}:{ri}:{pid or ''}:{port or ''}:{item.attrib.get('protocol','')}",host_name=hn,host_ip=p.get("host-ip"),host_fqdn=p.get("host-fqdn"),host_mac=p.get("mac-address"),host_uuid=p.get("host-uuid"),resolved_hostname=mapping(db,p,hn),plugin_id=pid,plugin_name=pname,plugin_family=item.attrib.get("pluginFamily"),severity=sev,cvss_score=score,protocol=item.attrib.get("protocol"),port=port,service_name=item.attrib.get("svc_name"),cve_ids=json.dumps(cves),description=direct(item,"description"),synopsis=direct(item,"synopsis"),solution=direct(item,"solution"),plugin_output=direct(item,"plugin_output"),references_text="\n".join(refs) or None,exploit_available=txt(item,["exploit_available"]),first_found=txt(item,["first_found"]),last_found=txt(item,["last_found"]),review_status="new"))
    if not new: raise ValueError("The report contains no ReportItem findings.")
    report.report_name=(section.attrib.get("name") or report.filename)[:255];report.host_count=len(hosts);report.finding_count=len(new);report.status="analysed";report.error_message=None;report.analysed_at=datetime.utcnow()
    db.add_all(new);db.commit();db.refresh(report)
    return {"report":impdict(report),"hosts":len(hosts),"findings":len(new)}

class FindingUpdate(BaseModel):
    severity:str|None=Field(default=None,max_length=20)
    cvss_score:float|None=Field(default=None,ge=0,le=10)
    description:str|None=None
    synopsis:str|None=None
    solution:str|None=None
    review_notes:str|None=None
class Review(BaseModel):
    status:str
    notes:str|None=None
class MappingCreate(BaseModel):
    match_type:str
    reported_value:str=Field(min_length=1,max_length=255)
    actual_hostname:str=Field(min_length=1,max_length=255)
    enabled:bool=True
    notes:str|None=None
class MappingUpdate(BaseModel):
    match_type:str|None=None
    reported_value:str|None=None
    actual_hostname:str|None=None
    enabled:bool|None=None
    notes:str|None=None
def mdict(x):return {"id":x.id,"match_type":x.match_type,"reported_value":x.reported_value,"actual_hostname":x.actual_hostname,"enabled":x.enabled,"notes":x.notes,"created_at":x.created_at,"updated_at":x.updated_at}

@router.post("/imports",status_code=201)
async def upload(file:UploadFile=File(...),db:Session=Depends(get_db)):
    name=(file.filename or "").strip()
    if not name.lower().endswith((".nessus",".xml")):raise HTTPException(400,"Upload a Nessus .nessus or .xml export.")
    raw=await file.read(MAX_BYTES+1)
    if not raw:raise HTTPException(400,"The uploaded file is empty.")
    if len(raw)>MAX_BYTES:raise HTTPException(413,"Nessus report exceeds 25 MB.")
    try:content=raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:raise HTTPException(400,"XML must be UTF-8 encoded.") from e
    x=NessusImport(filename=name[:255],raw_xml=content,status="uploaded");db.add(x);db.commit();db.refresh(x);return impdict(x)
@router.get("/imports")
def imports(limit:int=100,db:Session=Depends(get_db)):
    xs=db.scalars(select(NessusImport).order_by(NessusImport.uploaded_at.desc()).limit(max(1,min(limit,300)))).all()
    return {"items":[impdict(x) for x in xs],"total":len(xs)}
@router.post("/imports/{rid}/analyse")
def run_analysis(rid:int,db:Session=Depends(get_db)):
    x=db.get(NessusImport,rid)
    if not x:raise HTTPException(404,"Nessus import not found.")
    try:return analyse(db,x)
    except ValueError as e:x.status="analysis_failed";x.error_message=str(e);db.commit();raise HTTPException(400,str(e)) from e
@router.get("/results")
def results(status:str="all",q:str|None=None,limit:int=500,db:Session=Depends(get_db)):
    query=select(NessusFinding).order_by(NessusFinding.created_at.desc(),NessusFinding.id.desc())
    if status!="all":query=query.where(NessusFinding.review_status==status)
    if q:
        n=f"%{q.strip()}%";query=query.where(or_(NessusFinding.plugin_name.ilike(n),NessusFinding.plugin_id.ilike(n),NessusFinding.host_name.ilike(n),NessusFinding.host_ip.ilike(n),NessusFinding.resolved_hostname.ilike(n),NessusFinding.cve_ids.ilike(n),NessusFinding.description.ilike(n)))
    xs=db.scalars(query.limit(max(1,min(limit,1000)))).all();return {"items":[fdict(x) for x in xs],"total":len(xs)}
@router.get("/results/{fid}")
def result(fid:int,db:Session=Depends(get_db)):
    x=db.get(NessusFinding,fid)
    if not x:raise HTTPException(404,"Nessus finding not found.")
    return fdict(x)
@router.put("/results/{fid}")
def update_result(fid:int,data:FindingUpdate,db:Session=Depends(get_db)):
    x=db.get(NessusFinding,fid)
    if not x:raise HTTPException(404,"Nessus finding not found.")
    if x.review_status=="approved":raise HTTPException(409,"Accepted findings cannot be edited here.")
    for k,v in data.model_dump(exclude_unset=True).items():setattr(x,k,v)
    db.commit();db.refresh(x);return fdict(x)
@router.post("/results/{fid}/review")
def review(fid:int,data:Review,db:Session=Depends(get_db)):
    if data.status not in {"under_review","rejected"}:raise HTTPException(400,"Status must be under_review or rejected.")
    x=db.get(NessusFinding,fid)
    if not x:raise HTTPException(404,"Nessus finding not found.")
    if x.review_status=="approved":raise HTTPException(409,"Accepted finding cannot change status.")
    x.review_status=data.status;x.review_notes=data.notes;x.reviewed_at=datetime.utcnow();db.commit();return fdict(x)
@router.post("/results/{fid}/approve")
def approve(fid:int,db:Session=Depends(get_db)):
    x=db.get(NessusFinding,fid)
    if not x:raise HTTPException(404,"Nessus finding not found.")
    if x.review_status=="rejected":raise HTTPException(409,"Rejected finding cannot be accepted.")
    cves=sorted({v.upper() for v in json.loads(x.cve_ids or "[]") if re.fullmatch(r"CVE-\d{4}-\d{4,}",v,re.I)})
    if not cves:raise HTTPException(400,"This finding has no valid CVE reference and cannot enter the CVE Vulnerability Register.")
    report=db.get(NessusImport,x.import_id)
    evidence=f"Source report: {report.filename if report else 'Unknown'}\nHost: {x.resolved_hostname or x.host_name or x.host_ip or 'Unknown'}\nOriginal host: {x.host_name or 'Unknown'}\nPlugin ID: {x.plugin_id or 'Unknown'}\nPlugin: {x.plugin_name}\nPort: {x.port or 'N/A'}/{x.protocol or 'N/A'}\nSynopsis: {x.synopsis or ''}\nDescription: {x.description or ''}\nPlugin output:\n{x.plugin_output or ''}\nSolution: {x.solution or ''}"
    now=datetime.utcnow()
    for cve in cves:
        record=db.scalar(select(ThreatIntelligence).where(ThreatIntelligence.cve_id==cve))
        if record is None:
            db.add(ThreatIntelligence(cve_id=cve,severity=x.severity,cvss_score=x.cvss_score,affected_product=x.plugin_name,remediation=x.solution,description=x.description or x.synopsis,references_text=x.references_text,nvd_url=f"https://nvd.nist.gov/vuln/detail/{cve}",source_message=evidence[:30000],source_channel="Nessus Manual Scan",date=now,jira_status="not_sent",created_at=now,updated_at=now))
        else:
            for k,v in {"severity":x.severity,"cvss_score":x.cvss_score,"affected_product":x.plugin_name,"remediation":x.solution,"description":x.description or x.synopsis,"references_text":x.references_text}.items():
                if getattr(record,k) in (None,"") and v not in (None,""):setattr(record,k,v)
            if "Source report:" not in (record.source_message or ""):record.source_message=((record.source_message or "")+"\n\n"+evidence)[:30000]
            record.updated_at=now
    x.review_status="approved";x.reviewed_at=now;db.commit();return {"status":"approved","finding_id":x.id,"cve_ids":cves,"register_count":len(cves)}
@router.get("/host-mappings")
def mappings(db:Session=Depends(get_db)):
    xs=db.scalars(select(NessusHostMapping).order_by(NessusHostMapping.id.desc())).all();return {"items":[mdict(x) for x in xs],"total":len(xs)}
@router.post("/host-mappings",status_code=201)
def create_mapping(data:MappingCreate,db:Session=Depends(get_db)):
    if data.match_type not in {"hostname","fqdn","ip","mac","uuid"}:raise HTTPException(400,"Invalid match type.")
    if db.scalar(select(NessusHostMapping).where(NessusHostMapping.match_type==data.match_type,NessusHostMapping.reported_value.ilike(data.reported_value.strip()))):raise HTTPException(409,"A mapping already exists for this identifier type.")
    x=NessusHostMapping(**data.model_dump());x.reported_value=x.reported_value.strip();x.actual_hostname=x.actual_hostname.strip();db.add(x);db.commit();db.refresh(x);return mdict(x)
@router.put("/host-mappings/{mid}")
def update_mapping(mid:int,data:MappingUpdate,db:Session=Depends(get_db)):
    x=db.get(NessusHostMapping,mid)
    if not x:raise HTTPException(404,"Host mapping not found.")
    for k,v in data.model_dump(exclude_unset=True).items():setattr(x,k,v.strip() if isinstance(v,str) else v)
    x.updated_at=datetime.utcnow();db.commit();db.refresh(x);return mdict(x)
@router.delete("/host-mappings/{mid}",status_code=204)
def delete_mapping(mid:int,db:Session=Depends(get_db)):
    x=db.get(NessusHostMapping,mid)
    if not x:raise HTTPException(404,"Host mapping not found.")
    db.delete(x);db.commit()
