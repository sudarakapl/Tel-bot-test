import gspread
from gspread.exceptions import SpreadsheetNotFound, APIError
import datetime
import re
from oauth2client.service_account import ServiceAccountCredentials
from config import (
    SHEET_NAME,
    CREDENTIALS_FILE,
    GOOGLE_PROJECT_ID,
    GOOGLE_PRIVATE_KEY_ID,
    GOOGLE_PRIVATE_KEY,
    GOOGLE_CLIENT_EMAIL,
    GOOGLE_CLIENT_ID,
)
from date_parser import extract_due_date

# Define the scope
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def get_google_client():
    """Create and return authenticated Google Sheets client"""
    # Create credentials from environment variables

    credentials_dict = {
        "type": "service_account",
        "project_id": GOOGLE_PROJECT_ID,
        "private_key_id": GOOGLE_PRIVATE_KEY_ID,
        "private_key": GOOGLE_PRIVATE_KEY.replace("\\n", "\n"),
        "client_email": GOOGLE_CLIENT_EMAIL,
        "client_id": GOOGLE_CLIENT_ID,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{GOOGLE_CLIENT_EMAIL.replace('@', '%40')}",
    }

    # Use from_json_keyfile_dict instead of from_json_keyfile_name
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        credentials_dict,
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    client = gspread.authorize(credentials)
    return client


def get_or_create_spreadsheet():
    """Get the main spreadsheet or create it if it doesn't exist"""
    client = get_google_client()

    # Try to open existing spreadsheet
    try:
        spreadsheet = client.open(SHEET_NAME)
        spreadsheet.share(None, perm_type="anyone", role="writer")

        if "Sheet1" in spreadsheet.worksheets():
            spreadsheet.del_worksheet(spreadsheet.worksheet("Sheet1"))

        print(f"📊 Opened existing Google Sheet: {SHEET_NAME}")
    except gspread.exceptions.SpreadsheetNotFound:
        # Create new spreadsheet if not found
        spreadsheet = client.create(SHEET_NAME)
        print(f"📊 Created new Google Sheet: {SHEET_NAME}")

        if "Sheet1" in spreadsheet.worksheets():
            spreadsheet.del_worksheet(spreadsheet.worksheet("Sheet1"))

        # Make the spreadsheet accessible to anyone with the link (view only)
        spreadsheet.share(None, perm_type="anyone", role="writer")

        print(f"📊 Created new Google Sheet: {SHEET_NAME}")
        print(f"📊 Sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")

        # Add this after creating the spreadsheet
        try:
            # Publish the sheet to the web
            request = {
                "published": True,
                "publishAuto": True,
                "publishedLinkType": "PUBLISHED_LINK_TYPE_PUBLIC",
            }
            client.sh.batch_update(
                {
                    "requests": [
                        {
                            "updateSpreadsheetProperties": {
                                "properties": {"published": True},
                                "fields": "published",
                            }
                        }
                    ]
                }
            )
            print(
                f"📊 Published sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}/pubhtml"
            )
        except Exception as e:
            print(f"❌ Failed to publish sheet: {e}")

    return spreadsheet


def get_or_create_worksheet(spreadsheet, chat_name):
    """Get existing worksheet for a chat or create a new one"""
    # Sanitize worksheet name (Google Sheets has 100 char limit for tab names)
    sheet_name = sanitize_sheet_name(chat_name)

    # Try to get existing worksheet
    try:
        worksheet = spreadsheet.worksheet(sheet_name)
        print(f"📄 Using existing worksheet: {sheet_name}")
    except gspread.exceptions.WorksheetNotFound:
        # Create new worksheet
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=8)

        # Add headers
        headers = [
            "#",
            "Category",
            "Task / Description",
            "Sub-Tasks / Notes",
            "Owner",
            "Due Date",
            "Status",
            "Created Date",
        ]
        worksheet.append_row(headers)

        # Format header row (bold, background color)
        format_header_row(spreadsheet, worksheet)

        # Set column widths
        set_column_widths(spreadsheet, worksheet)

        print(f"📄 Created new worksheet: {sheet_name}")

    return worksheet


def format_header_row(spreadsheet, worksheet):
    """Apply formatting to the header row"""
    worksheet_id = worksheet.id

    # Format header row (bold, background color)
    fmt = {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.85, "green": 0.88, "blue": 0.95},
        "horizontalAlignment": "CENTER",
    }

    format_request = {
        "repeatCell": {
            "range": {"sheetId": worksheet_id, "startRowIndex": 0, "endRowIndex": 1},
            "cell": {"userEnteredFormat": fmt},
            "fields": "userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)",
        }
    }

    # Apply borders
    border_request = {
        "updateBorders": {
            "range": {
                "sheetId": worksheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "top": {"style": "SOLID"},
            "bottom": {"style": "SOLID"},
            "left": {"style": "SOLID"},
            "right": {"style": "SOLID"},
            "innerHorizontal": {"style": "SOLID"},
            "innerVertical": {"style": "SOLID"},
        }
    }

    # Apply freeze for header row
    freeze_request = {
        "updateSheetProperties": {
            "properties": {
                "sheetId": worksheet_id,
                "gridProperties": {"frozenRowCount": 1},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    }

    spreadsheet.batch_update(
        {"requests": [format_request, border_request, freeze_request]}
    )


def set_column_widths(spreadsheet, worksheet):
    """Set column widths for better readability"""
    worksheet_id = worksheet.id

    # Define column widths (in pixels)
    col_widths = [70, 100, 400, 250, 100, 100, 100, 120]

    requests = []
    for i, width in enumerate(col_widths):
        requests.append(
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": i,
                        "endIndex": i + 1,
                    },
                    "properties": {"pixelSize": width},
                    "fields": "pixelSize",
                }
            }
        )

    spreadsheet.batch_update({"requests": requests})


def sanitize_sheet_name(name):
    """Make sheet name compatible with Google Sheets"""
    # Remove invalid characters
    name = re.sub(r"[\\/*\[\]:]", "_", name)

    # Limit to 100 characters (Google Sheets limit)
    if len(name) > 100:
        name = name[:100]

    # Ensure not empty
    if not name:
        name = "Default"

    return name


def get_next_task_number(worksheet):
    """Get the next task number for the worksheet"""
    values = worksheet.get_all_values()
    if len(values) <= 1:  # Only header row exists
        return 1
    return len(values)  # Already 1-indexed because of header row


def append_task_to_sheet(task, from_user, full_message, chat_name, chat_id=None):
    """Add a task to the Google Sheet worksheet for the specific chat"""
    try:
        # Get timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extract due date or use default
        due_date = extract_due_date(task)
        if not due_date:
            due_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime(
                "%Y-%m-%d"
            )

        # Get category
        category = _get_task_category(task)

        # Get or create spreadsheet and worksheet
        spreadsheet = get_or_create_spreadsheet()
        worksheet = get_or_create_worksheet(spreadsheet, chat_name)

        # Get next task number
        task_number = get_next_task_number(worksheet)

        # Add task row
        worksheet.append_row(
            [
                task_number,
                category,
                task,
                "",  # Sub-tasks
                from_user,
                due_date,
                "New",
                timestamp,
            ]
        )

        # Format the task row
        format_task_row(spreadsheet, worksheet, task_number)

        print(
            f"✅ Task added to Google Sheet ({chat_name}): '{task[:30]}...' from {from_user}"
        )
        return True
    except Exception as e:
        print(f"❌ Failed to write to Google Sheet: {e}")
        return False


def format_task_row(spreadsheet, worksheet, row_num):
    """Format a task row with borders and center alignment for certain cells"""
    worksheet_id = worksheet.id

    # Add borders to the row
    border_request = {
        "updateBorders": {
            "range": {
                "sheetId": worksheet_id,
                "startRowIndex": row_num,
                "endRowIndex": row_num + 1,
                "startColumnIndex": 0,
                "endColumnIndex": 8,
            },
            "top": {"style": "SOLID"},
            "bottom": {"style": "SOLID"},
            "left": {"style": "SOLID"},
            "right": {"style": "SOLID"},
            "innerVertical": {"style": "SOLID"},
        }
    }

    # Center alignment for specific columns
    center_columns = [
        0,
        1,
        4,
        5,
        6,
        7,
    ]  # 0-indexed: #, Category, Owner, Due Date, Status, Created Date

    center_requests = []
    for col in center_columns:
        center_requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": worksheet_id,
                        "startRowIndex": row_num,
                        "endRowIndex": row_num + 1,
                        "startColumnIndex": col,
                        "endColumnIndex": col + 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE",
                        }
                    },
                    "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)",
                }
            }
        )

    # Apply all formatting
    requests = [border_request] + center_requests
    spreadsheet.batch_update({"requests": requests})


def _get_task_category(task):
    """Determine the category of a task based on its content"""
    task_lower = task.lower()

    if "meeting" in task_lower or "call" in task_lower:
        return "Meeting"
    elif "review" in task_lower or "check" in task_lower:
        return "Review"
    elif "report" in task_lower or "document" in task_lower:
        return "Documentation"
    elif "approval" in task_lower:
        return "Approval"
    else:
        return "General"


def get_spreadsheet_url():
    """Get the URL of the spreadsheet for sharing"""
    try:
        client = get_google_client()

        # Try to open the spreadsheet
        try:
            spreadsheet = client.open(SHEET_NAME)
            print(f"📊 Opened existing Google Sheet: {SHEET_NAME}")
        except SpreadsheetNotFound:
            # Create a new spreadsheet if it doesn't exist
            spreadsheet = client.create(SHEET_NAME)

            # Make the spreadsheet accessible to anyone with the link (view only)
            spreadsheet.share(None, perm_type="anyone", role="reader")

            print(f"📊 Created new Google Sheet: {SHEET_NAME}")

        return f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
    except Exception as e:
        print(f"❌ Failed to get spreadsheet URL: {e}")
        return None


def get_all_worksheets():
    """Get all worksheet names in the spreadsheet"""
    try:
        spreadsheet = get_or_create_spreadsheet()
        worksheets = spreadsheet.worksheets()
        return [ws.title for ws in worksheets]
    except Exception as e:
        print(f"❌ Failed to get worksheets: {e}")
        return []


def get_worksheet_summary(worksheet_name=None):
    """Get task count summary for all or specific worksheet"""
    try:
        spreadsheet = get_or_create_spreadsheet()

        if worksheet_name:
            # Get summary for specific worksheet
            worksheet = spreadsheet.worksheet(worksheet_name)
            values = worksheet.get_all_values()
            return len(values) - 1 if len(values) > 0 else 0
        else:
            # Get summary for all worksheets
            summary = {}
            for ws in spreadsheet.worksheets():
                values = ws.get_all_values()
                summary[ws.title] = len(values) - 1 if len(values) > 0 else 0
            return summary
    except Exception as e:
        print(f"❌ Failed to get worksheet summary: {e}")
        return {} if worksheet_name is None else 0
