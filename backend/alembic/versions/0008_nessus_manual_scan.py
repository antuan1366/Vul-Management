"""Add Nessus import/review and host mapping tables."""
from typing import Sequence,Union
from alembic import op
import sqlalchemy as sa
revision:str="0008"
down_revision:Union[str,Sequence[str],None]="0007"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("nessus_imports",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("filename",sa.String(255),nullable=False),sa.Column("report_name",sa.String(255)),sa.Column("status",sa.String(30),nullable=False,server_default="uploaded"),sa.Column("raw_xml",sa.Text(),nullable=False),sa.Column("host_count",sa.Integer(),nullable=False,server_default="0"),sa.Column("finding_count",sa.Integer(),nullable=False,server_default="0"),sa.Column("error_message",sa.Text()),sa.Column("uploaded_at",sa.DateTime(),nullable=False),sa.Column("analysed_at",sa.DateTime()))
    for col in ("id","status"):op.create_index(f"ix_nessus_imports_{col}","nessus_imports",[col])
    op.create_table("nessus_findings",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("import_id",sa.Integer(),sa.ForeignKey("nessus_imports.id",ondelete="CASCADE"),nullable=False),sa.Column("finding_key",sa.String(200),nullable=False),sa.Column("host_name",sa.String(255)),sa.Column("host_ip",sa.String(100)),sa.Column("host_fqdn",sa.String(255)),sa.Column("host_mac",sa.String(100)),sa.Column("host_uuid",sa.String(100)),sa.Column("resolved_hostname",sa.String(255)),sa.Column("plugin_id",sa.String(50)),sa.Column("plugin_name",sa.Text(),nullable=False),sa.Column("plugin_family",sa.String(255)),sa.Column("severity",sa.String(20),nullable=False,server_default="Info"),sa.Column("cvss_score",sa.Float()),sa.Column("protocol",sa.String(20)),sa.Column("port",sa.Integer()),sa.Column("service_name",sa.String(100)),sa.Column("cve_ids",sa.Text(),nullable=False,server_default="[]"),sa.Column("description",sa.Text()),sa.Column("synopsis",sa.Text()),sa.Column("solution",sa.Text()),sa.Column("plugin_output",sa.Text()),sa.Column("references_text",sa.Text()),sa.Column("exploit_available",sa.String(20)),sa.Column("first_found",sa.String(100)),sa.Column("last_found",sa.String(100)),sa.Column("review_status",sa.String(20),nullable=False,server_default="new"),sa.Column("review_notes",sa.Text()),sa.Column("reviewed_at",sa.DateTime()),sa.Column("created_at",sa.DateTime(),nullable=False))
    for col in ("id","import_id","host_name","host_ip","host_fqdn","plugin_id","severity","review_status","resolved_hostname","finding_key"):op.create_index(f"ix_nessus_findings_{col}","nessus_findings",[col])
    op.create_table("nessus_host_mappings",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("match_type",sa.String(30),nullable=False,server_default="hostname"),sa.Column("reported_value",sa.String(255),nullable=False),sa.Column("actual_hostname",sa.String(255),nullable=False),sa.Column("enabled",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("notes",sa.Text()),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("updated_at",sa.DateTime(),nullable=False))
    for col in ("id","reported_value","actual_hostname"):op.create_index(f"ix_nessus_host_mappings_{col}","nessus_host_mappings",[col])
def downgrade():
    op.drop_table("nessus_host_mappings");op.drop_table("nessus_findings");op.drop_table("nessus_imports")
