from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
WORKBOOK_PATH = DATA_DIR / "Workbook.xlsx"
TEMPLATE_PATH = DATA_DIR / "Workbook_TEMPLATE.xlsx"
BACKUP_DIR = DATA_DIR / "backups"

MODULES = {
    "weekly-review": {"sheet": "Weekly Review", "header_row": 5, "start_col": 1, "presales": "Presales", "serial": None,
        "fields": ["Region", "AM", "Presales", "Customer", "Date of Opportunity (MM/YY)", "Opportunity Details", "NN/EC (New Opportunity/Existing Customer)", "Value (₹)", "OEM", "Stage", "Expected Closure (QTR)", "Month", "Remarks", "Week 1", "Week 2", "Week 3", "Week 4"]},
    "weekly-meeting": {"sheet": "Weekly meeting", "header_row": 5, "start_col": 1, "presales": "Presales", "serial": "Sr. No.",
        "fields": ["Sr. No.", "Region", "Month", "Week", "Date", "Presales", "Client Manager", "Account Name", "Account Type(New/Existing)", "Meeting Mode (In-Person/Virtual)", "Meeting Agenda", "Discussion Points", "Action Items", "Remarks"]},
    "training-attended": {"sheet": "Training Attended", "header_row": 5, "start_col": 1, "presales": "PreSales Name", "serial": "Sr No.",
        "fields": ["Sr No.", "Region", "Date", "PreSales Name", "Training Name", "OEM", "Technology Vertical", "Certification Done"]},
    "training-conducted": {"sheet": "Training Conducted", "header_row": 5, "start_col": 1, "presales": "PreSales Name", "serial": "Sr No.",
        "fields": ["Sr No.", "Region", "Date", "PreSales Name", "Training Name", "OEM", "Technology Vertical", "Certification"]},
    "poc": {"sheet": "PoC Tracker", "header_row": 5, "start_col": 1, "presales": "Presales", "serial": "Sr. No.",
        "fields": ["Sr. No.", "Region", "Date", "Presales", "Client Manager", "Customer", "PoC Details", "OEM", "Expected Completion Date", "Month", "Week 1", "Week 2", "Week 3", "Week 4"]},
    "customer-workshop": {"sheet": "Customer Workshop", "header_row": 5, "start_col": 1, "presales": "Presales", "serial": "Sr. No.",
        "fields": ["Sr. No.", "Region", "Date", "Presales", "Client Manager", "Customer", "Workshop Details", "OEM", "Month"]},
    "win-lost": {"sheet": "Win-Lost", "header_row": 3, "start_col": 2, "presales": "Presales", "serial": None,
        "fields": ["PO Date", "Region", "Presales", "Account Name", "Win/Lost", "Deal Value", "Remark"]},
}

STATUS_FIELDS = {"weekly-review": "Weekly Review", "weekly-meeting": "Weekly Meeting", "training-attended": "Training Attended", "training-conducted": "Training Conducted", "poc": "PoC Tracker", "customer-workshop": "Customer Workshop"}
