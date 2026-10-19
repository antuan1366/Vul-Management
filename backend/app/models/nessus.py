from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class NessusImport(Base):
    __tablename__="nessus_imports"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    filename: Mapped[str]=mapped_column(String(255),nullable=False)
    report_name: Mapped[str|None]=mapped_column(String(255))
    status: Mapped[str]=mapped_column(String(30),nullable=False,default="uploaded",index=True)
    raw_xml: Mapped[str]=mapped_column(Text,nullable=False)
    host_count: Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    finding_count: Mapped[int]=mapped_column(Integer,nullable=False,default=0)
    error_message: Mapped[str|None]=mapped_column(Text)
    uploaded_at: Mapped[datetime]=mapped_column(DateTime,nullable=False,default=datetime.utcnow)
    analysed_at: Mapped[datetime|None]=mapped_column(DateTime)

class NessusFinding(Base):
    __tablename__="nessus_findings"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    import_id: Mapped[int]=mapped_column(ForeignKey("nessus_imports.id",ondelete="CASCADE"),nullable=False,index=True)
    finding_key: Mapped[str]=mapped_column(String(200),nullable=False)
    host_name: Mapped[str|None]=mapped_column(String(255),index=True)
    host_ip: Mapped[str|None]=mapped_column(String(100),index=True)
    host_fqdn: Mapped[str|None]=mapped_column(String(255),index=True)
    host_mac: Mapped[str|None]=mapped_column(String(100))
    host_uuid: Mapped[str|None]=mapped_column(String(100))
    resolved_hostname: Mapped[str|None]=mapped_column(String(255),index=True)
    plugin_id: Mapped[str|None]=mapped_column(String(50),index=True)
    plugin_name: Mapped[str]=mapped_column(Text,nullable=False)
    plugin_family: Mapped[str|None]=mapped_column(String(255))
    severity: Mapped[str]=mapped_column(String(20),nullable=False,default="Info",index=True)
    cvss_score: Mapped[float|None]=mapped_column(Float)
    protocol: Mapped[str|None]=mapped_column(String(20))
    port: Mapped[int|None]=mapped_column(Integer)
    service_name: Mapped[str|None]=mapped_column(String(100))
    cve_ids: Mapped[str]=mapped_column(Text,nullable=False,default="[]")
    description: Mapped[str|None]=mapped_column(Text)
    synopsis: Mapped[str|None]=mapped_column(Text)
    solution: Mapped[str|None]=mapped_column(Text)
    plugin_output: Mapped[str|None]=mapped_column(Text)
    references_text: Mapped[str|None]=mapped_column(Text)
    exploit_available: Mapped[str|None]=mapped_column(String(20))
    first_found: Mapped[str|None]=mapped_column(String(100))
    last_found: Mapped[str|None]=mapped_column(String(100))
    review_status: Mapped[str]=mapped_column(String(20),nullable=False,default="new",index=True)
    review_notes: Mapped[str|None]=mapped_column(Text)
    reviewed_at: Mapped[datetime|None]=mapped_column(DateTime)
    created_at: Mapped[datetime]=mapped_column(DateTime,nullable=False,default=datetime.utcnow)

class NessusHostMapping(Base):
    __tablename__="nessus_host_mappings"
    id: Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    match_type: Mapped[str]=mapped_column(String(30),nullable=False,default="hostname")
    reported_value: Mapped[str]=mapped_column(String(255),nullable=False,index=True)
    actual_hostname: Mapped[str]=mapped_column(String(255),nullable=False,index=True)
    enabled: Mapped[bool]=mapped_column(Boolean,nullable=False,default=True)
    notes: Mapped[str|None]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime,nullable=False,default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)
