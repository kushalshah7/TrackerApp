from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

MODULES = {
    "weekly-review": {"presales": "Presales", "serial": None, "fields": ["Region", "AM", "Presales", "Customer", "Date of Opportunity (MM/YY)", "Opportunity Details", "NN/EC (New Opportunity/Existing Customer)", "Value (â‚¹)", "OEM", "Stage", "Expected Closure (QTR)", "Month", "Remarks", "Week 1", "Week 2", "Week 3", "Week 4"]},
    "weekly-meeting": {"presales": "Presales", "serial": "Sr. No.", "fields": ["Sr. No.", "Region", "Month", "Week", "Date", "Presales", "Client Manager", "Account Name", "Account Type(New/Existing)", "Meeting Mode (In-Person/Virtual)", "Meeting Agenda", "Discussion Points", "Action Items", "Remarks"]},
    "training-attended": {"presales": "PreSales Name", "serial": "Sr No.", "fields": ["Sr No.", "Region", "Date", "PreSales Name", "Training Name", "OEM", "Technology Vertical", "Certification Done"]},
    "training-conducted": {"presales": "PreSales Name", "serial": "Sr No.", "fields": ["Sr No.", "Region", "Date", "PreSales Name", "Training Name", "OEM", "Technology Vertical", "Certification"]},
    "poc": {"presales": "Presales", "serial": "Sr. No.", "fields": ["Sr. No.", "Region", "Date", "Presales", "Client Manager", "Customer", "PoC Details", "OEM", "Expected Completion Date", "Month", "Week 1", "Week 2", "Week 3", "Week 4"]},
    "customer-workshop": {"presales": "Presales", "serial": "Sr. No.", "fields": ["Sr. No.", "Region", "Date", "Presales", "Client Manager", "Customer", "Workshop Details", "OEM", "Month"]},
    "win-lost": {"presales": "Presales", "serial": None, "fields": ["PO Date", "Region", "Presales", "Account Name", "Win/Lost", "Deal Value", "Remark"]},
}
MODULES["weekly-review"]["sheet"] = "Presales Review"
MODULES["weekly-review"]["fields"][7] = "Value (₹)"
MODULES["weekly-review"]["fields"][11] = "Expected Month"
MODULES["weekly-meeting"]["sheet"] = "Presales"

REQUIRED_FIELDS = {
    "weekly-review": {"Region", "Presales", "Customer", "Opportunity Details"},
    "weekly-meeting": {"Region", "Date", "Presales", "Account Name", "Meeting Agenda"},
    "training-attended": {"Region", "Date", "PreSales Name", "Training Name"},
    "training-conducted": {"Region", "Date", "PreSales Name", "Training Name"},
    "poc": {"Region", "Date", "Presales", "Customer", "PoC Details"},
    "customer-workshop": {"Region", "Date", "Presales", "Customer", "Workshop Details"},
    "win-lost": {"PO Date", "Region", "Presales", "Account Name", "Win/Lost"},
}

def validate_entry_data(module: str, data: dict) -> None:
    missing = sorted(field for field in REQUIRED_FIELDS[module] if data.get(field) in (None, ""))
    if missing:
        raise ValueError(f"Required fields missing: {', '.join(missing)}")

@dataclass(frozen=True)
class Settings:
    tenant_id: str
    backend_client_id: str
    backend_client_secret: str
    api_audience: str
    graph_scope: str
    sharepoint_workbook_share_url: str
    excel_table_name: str
    record_id_column: str
    frontend_origin: str

    @classmethod
    def from_env(cls, require_all: bool = True) -> "Settings":
        mapping = {
            "tenant_id": ("ENTRA_TENANT_ID", ""),
            "backend_client_id": ("ENTRA_BACKEND_CLIENT_ID", ""),
            "backend_client_secret": ("ENTRA_BACKEND_CLIENT_SECRET", ""),
            "api_audience": ("ENTRA_API_AUDIENCE", ""),
            "graph_scope": ("GRAPH_SCOPE", "https://graph.microsoft.com/Files.ReadWrite"),
            "sharepoint_workbook_share_url": ("SHAREPOINT_WORKBOOK_SHARE_URL", ""),
            "excel_table_name": ("EXCEL_TABLE_NAME", "PresalesRecords"),
            "record_id_column": ("EXCEL_RECORD_ID_COLUMN", "Record ID"),
            "frontend_origin": ("FRONTEND_ORIGIN", "http://localhost:5173"),
        }
        values = {key: os.getenv(env, default) for key, (env, default) in mapping.items()}
        if require_all:
            missing = [env for key, (env, _) in mapping.items() if key in {"tenant_id", "backend_client_id", "backend_client_secret", "api_audience", "sharepoint_workbook_share_url"} and not values[key]]
            if missing:
                raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")
        return cls(**values)

def required_table_headers(settings: Settings) -> list[str]:
    headers = [settings.record_id_column, "Module"]
    for cfg in MODULES.values():
        for field in cfg["fields"]:
            if field not in headers:
                headers.append(field)
    return headers
