"""
Google Calendar service — authenticates via OAuth2 and fetches events
matching a client name within a date range.
"""

import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only calendar access
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")


def _get_calendar_service():
    """Authenticate and return a Google Calendar API service instance."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Google OAuth credentials not found at {CREDENTIALS_FILE}. "
                    "Please download credentials.json from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def get_appointments(client_name, start_date, end_date):
    """
    Fetch calendar events that contain `client_name` in the summary,
    between start_date and end_date (inclusive).

    Args:
        client_name: str — the client name to search for
        start_date:  str — ISO date string (YYYY-MM-DD)
        end_date:    str — ISO date string (YYYY-MM-DD)

    Returns:
        list of dicts with keys: date, day, start_time, end_time, duration_hours,
        duration_display, description
    """
    service = _get_calendar_service()

    # Convert to RFC3339 with timezone
    time_min = f"{start_date}T00:00:00Z"
    time_max = f"{end_date}T23:59:59Z"

    all_events = []
    page_token = None

    while True:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
            pageToken=page_token,
        ).execute()

        events = events_result.get("items", [])

        for event in events:
            summary = event.get("summary", "")
            # Case-insensitive partial match
            if client_name.lower() in summary.lower():
                appointment = _parse_event(event)
                if appointment:
                    all_events.append(appointment)

        page_token = events_result.get("nextPageToken")
        if not page_token:
            break

    return all_events


def _parse_event(event):
    """Parse a Google Calendar event into an appointment dict."""
    start_raw = event["start"].get("dateTime", event["start"].get("date"))
    end_raw = event["end"].get("dateTime", event["end"].get("date"))

    # Skip all-day events (no dateTime, only date)
    if "dateTime" not in event["start"]:
        return None

    start_dt = datetime.datetime.fromisoformat(start_raw)
    end_dt = datetime.datetime.fromisoformat(end_raw)

    duration = end_dt - start_dt
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    # Duration as decimal hours for calculation
    duration_hours = round(total_seconds / 3600, 2)

    # Day of week names in French
    days_fr = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche",
    }

    return {
        "date": start_dt.strftime("%d-%m-%Y"),
        "day": days_fr.get(start_dt.weekday(), ""),
        "start_time": start_dt.strftime("%H:%M"),
        "end_time": end_dt.strftime("%H:%M"),
        "duration_hours": duration_hours,
        "duration_display": f"{hours}:{minutes:02d}",
        "description": event.get("summary", ""),
    }
