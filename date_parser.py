import re
import datetime


def extract_due_date(task_text):
    """Extract due date from task text if mentioned"""
    # Common date patterns
    date_patterns = [
        r"by\s+(tomorrow|today|next\s+week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        r"due\s+(on\s+)?(tomorrow|today|next\s+week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        r"(on|by)\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:st|nd|rd|th)?)",
        r"(this|next)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
        r"end\s+of\s+(week|month)",
    ]

    for pattern in date_patterns:
        match = re.search(pattern, task_text.lower())
        if match:
            date_text = match.group(0)
            today = datetime.datetime.now()

            if "tomorrow" in date_text:
                return (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            elif "today" in date_text:
                return today.strftime("%Y-%m-%d")
            elif "next week" in date_text:
                return (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            elif "end of week" in date_text:
                days_until_friday = (4 - today.weekday()) % 7
                if days_until_friday == 0:
                    days_until_friday = 7
                return (today + datetime.timedelta(days=days_until_friday)).strftime(
                    "%Y-%m-%d"
                )
            elif "end of month" in date_text:
                next_month = today.replace(day=28) + datetime.timedelta(days=4)
                last_day = next_month - datetime.timedelta(days=next_month.day)
                return last_day.strftime("%Y-%m-%d")

            # Handle day names
            for i, day in enumerate(
                [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]
            ):
                if day in date_text:
                    days_until = (i - today.weekday()) % 7
                    if "next" in date_text:
                        days_until += 7
                    if days_until == 0 and "this" not in date_text:
                        days_until = 7
                    return (today + datetime.timedelta(days=days_until)).strftime(
                        "%Y-%m-%d"
                    )

    return None
