from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset_field import AssetFieldDefinition


DEFAULT_MANAGED_ASSET_FIELDS = {
    "operating_system": [
        ("name", "Name", "text", True, "Operating system name."),
        ("equipment_id", "Equipment ID", "number", False, "Optional related equipment ID."),
        ("vendor", "Vendor", "text", True, "Operating system vendor."),
        ("version", "Version", "text", True, "Operating system version."),
        ("edition", "Edition", "text", False, "Operating system edition."),
        ("build", "Build", "text", False, "Operating system build number."),
        ("architecture", "Architecture", "text", False, "CPU architecture."),
        ("kernel", "Kernel", "text", False, "Kernel version."),
        ("cpe", "CPE", "text", False, "Common Platform Enumeration identifier."),
        ("install_date", "Install Date", "date", False, "Installation date."),
        ("support_end_date", "Support End Date", "date", False, "End of vendor support."),
        ("lifecycle_status", "Lifecycle Status", "select", False, "Current lifecycle state."),
        ("description", "Description", "textarea", False, "Additional information."),
    ],
    "application": [
        ("name", "Name", "text", True, "Application name."),
        ("vendor", "Vendor", "text", True, "Application vendor."),
        ("version", "Version", "text", True, "Application version."),
        ("edition", "Edition", "text", False, "Application edition."),
        ("platform", "Platform", "text", False, "Operating system or platform."),
        ("install_path", "Install Path", "text", False, "Installation path."),
        ("cpe", "CPE", "text", False, "Common Platform Enumeration identifier."),
        ("owner", "Owner", "text", False, "Application owner or responsible team."),
        ("criticality", "Criticality", "select", True, "Business/security criticality."),
        ("environment", "Environment", "select", True, "Deployment environment."),
        ("description", "Description", "textarea", False, "Additional information."),
    ],
    "library": [
        ("name", "Name", "text", True, "Library/package name."),
        ("version", "Version", "text", True, "Library/package version."),
        ("language", "Language", "text", False, "Programming language."),
        ("package_manager", "Package Manager", "text", False, "Package manager."),
        ("package_identifier", "Package Identifier", "text", False, "Native package identifier."),
        ("purl", "Package URL (PURL)", "text", False, "Package URL identifier."),
        ("repository", "Repository", "url", False, "Source/package repository URL."),
        ("vendor", "Vendor", "text", False, "Library vendor or publisher."),
        ("cpe", "CPE", "text", False, "Common Platform Enumeration identifier."),
        ("description", "Description", "textarea", False, "Additional information."),
    ],
}


def seed_managed_asset_fields(db: Session) -> None:
    changed = False

    for asset_type, definitions in DEFAULT_MANAGED_ASSET_FIELDS.items():
        existing_keys = set(
            db.scalars(
                select(AssetFieldDefinition.field_key).where(
                    AssetFieldDefinition.asset_type == asset_type
                )
            ).all()
        )

        for field_key, label, field_type, required, description in definitions:
            if field_key in existing_keys:
                continue

            options = None

            if field_key == "lifecycle_status":
                options = '["Active", "Extended Support", "End of Life", "Unknown"]'

            if field_key == "criticality":
                options = '["Critical", "High", "Medium", "Low"]'

            if field_key == "environment":
                options = '["Production", "DR", "Test", "Development"]'

            db.add(
                AssetFieldDefinition(
                    asset_type=asset_type,
                    field_key=field_key,
                    label=label,
                    field_type=field_type,
                    required=required,
                    visible=True,
                    system_field=True,
                    editable=True,
                    deletable=False,
                    options=options,
                    description=description,
                )
            )
            changed = True

    if changed:
        db.commit()
