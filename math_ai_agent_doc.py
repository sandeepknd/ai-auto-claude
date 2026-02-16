# ✅ Claude-Powered Tool-Calling Agent
# Uses Anthropic's Claude API for fast, reliable AI responses

import json
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from PyPDF2 import PdfReader
import smtplib
from email.message import EmailMessage
import re
from email.mime.text import MIMEText
import base64
from gmail_auth import get_gmail_service
from fastapi.responses import JSONResponse
from datetime import datetime
import dateparser
from bs4 import BeautifulSoup

# Import Claude CLI client instead of Claude API
from claude_cli_client import call_llm

import requests
# === STEP 1: Define local tools ===
def add_numbers(numbers):
    print("[DEBUG] add_numbers() called")
    return sum(numbers)

def subtract(a, b):
    print("[DEBUG] subtract() called")
    return a - b

def multiply(numbers):
    print("[DEBUG] multiply() called")
    result = 1
    for n in numbers:
        result *= n
    return result

def divide(a, b):
    print("[DEBUG] divide() called")
    if b == 0:
        return "Error: Division by zero"
    return a / b

def get_weather(city):
    """
    Get real-time weather data for a city using wttr.in free weather service.
    No API key required!

    Args:
        city: City name (e.g., "Paris", "New York", "London")

    Returns:
        Formatted weather information string
    """
    print(f"[DEBUG] get_weather() called with city={city}")

    try:
        # wttr.in API endpoint (completely free, no API key required!)
        # Format: wttr.in/{city}?format=j1 for JSON output
        base_url = f"https://wttr.in/{city}"

        # Parameters for the API request
        params = {
            "format": "j1"  # JSON format
        }

        # Headers to identify as a script/bot (recommended by wttr.in)
        headers = {
            "User-Agent": "curl/7.68.0"
        }

        # Make the API request
        response = requests.get(base_url, params=params, headers=headers, timeout=10)

        # Check if request was successful
        if response.status_code == 404:
            return f"❌ City '{city}' not found. Please check the spelling."

        if response.status_code != 200:
            return f"❌ Weather service error (Status: {response.status_code})"

        # Parse the JSON response
        data = response.json()

        # Extract current weather information
        current = data["current_condition"][0]
        location = data["nearest_area"][0]

        # Get location details
        area_name = location["areaName"][0]["value"]
        country = location["country"][0]["value"]

        # Get weather details
        temp_c = current["temp_C"]
        feels_like_c = current["FeelsLikeC"]
        humidity = current["humidity"]
        description = current["weatherDesc"][0]["value"]
        wind_speed_kmph = current["windspeedKmph"]
        wind_dir = current["winddir16Point"]
        pressure = current["pressure"]
        visibility = current["visibility"]

        # Format the response
        weather_info = (
            f"🌤️ Weather in {area_name}, {country}:\n"
            f"  Temperature: {temp_c}°C (feels like {feels_like_c}°C)\n"
            f"  Condition: {description}\n"
            f"  Humidity: {humidity}%\n"
            f"  Wind: {wind_speed_kmph} km/h {wind_dir}\n"
            f"  Pressure: {pressure} mb\n"
            f"  Visibility: {visibility} km"
        )

        return weather_info

    except requests.exceptions.Timeout:
        return f"❌ Weather service timeout. Please try again."
    except requests.exceptions.ConnectionError:
        return f"❌ Cannot connect to weather service. Check your internet connection."
    except KeyError as e:
        print(f"[ERROR] Unexpected weather data format: {str(e)}")
        return f"❌ City '{city}' not found or weather data unavailable."
    except Exception as e:
        print(f"[ERROR] Weather API error: {str(e)}")
        return f"❌ Error fetching weather data: {str(e)}"

def analyze_document(path):
    print(f"[DEBUG] analyze_document() called with path={path}")
    file_path = Path(path)

    if not file_path.exists():
        return f"File not found: {path}"
        
    # Read text based on file type
    if file_path.suffix.lower() == ".txt":
        text = file_path.read_text(encoding="utf-8")
    elif file_path.suffix.lower() == ".pdf":
        reader = PdfReader(str(file_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        return "Unsupported file type. Only .txt and .pdf are supported."

    # Send summary request to Claude
    print("[INFO] Sending document content for summarization...")
    prompt = f"Please summarize or analyze the following document content:\n{text[:4000]}"  # Truncate for safety
    response = call_claude(prompt)
    return response.strip()

def send_email(to_address: str, subject: str, body: str):
    service = get_gmail_service()

    message = MIMEText(body)
    message['to'] = to_address
    message['from'] = "me"
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {'raw': raw}

    send_result = service.users().messages().send(userId="me", body=message_body).execute()
    print("send_result is {}".format(send_result))
    return f"✅ Email sent! ID: {send_result['id']}"

def email_agent(query: str) -> str:
    # Updated regex with non-greedy and greedy match groups
    pattern = r"send email to (?P<to>.+?) subject (?P<subject>.+) body (?P<body>.+)"
    match = re.match(pattern, query, re.IGNORECASE)
    if not match:
        return "❌ Could not parse the email format. Use: send email to [recipient] subject [subject] body [message]."

    try:
        to = match.group("to").strip()
        subject = match.group("subject").strip()
        body = match.group("body").strip()
        return send_email(to, subject, body)
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"

def mark_email(mail_sub: str, mark_as_read: bool):
    service = get_gmail_service()
    results = service.users().messages().list(userId="me", q=f"subject:{mail_sub}", maxResults=1).execute()
    messages = results.get("messages", [])

    if not messages:
        raise HTTPException(status_code=404, detail="Email not found.")

    msg_id = messages[0]["id"]

    if mark_as_read:
        service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        return {"status": f"Email with subject '{mail_sub}' marked as read."}
    else:
        service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"addLabelIds": ["UNREAD"]}
        ).execute()
        return f"✅ Email with subject '{mail_sub}' marked as unread."

def list_messages():
    service = get_gmail_service()
    resp = service.users().messages().list(userId="me", maxResults=25).execute()
    msgs = resp.get("messages", [])
    out = []
    for m in msgs:
        mdata = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["Subject", "From"]
            ).execute()
        headers = {h["name"]: h["value"] for h in mdata.get("payload", {}).get("headers", [])}
        out.append({
            "id": m["id"],
            "snippet": mdata.get("snippet", ""),
            "labelIds": mdata.get("labelIds", []),
            "subject": headers.get("Subject"),
            "from": headers.get("From"),
        })
    return {"messages": out}

def search_email_by_subject(service, subject):
    query = f'subject:"{subject}"'
    results = service.users().messages().list(userId="me", q=query, maxResults=1).execute()
    messages = results.get("messages", [])
    if not messages:
        raise HTTPException(status_code=404, detail="Email not found.")

    return messages[0]["id"]

def get_email_body(service, message_id):
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    payload = msg["payload"]
    parts = payload.get("parts", [])
   
    body_data = ""
    if parts:
        for part in parts:
            if part["mimeType"] == "text/plain":
                body_data = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
            elif part["mimeType"] == "text/html":
                html_data = part["body"].get("data")
                if html_data:
                    decoded_html = base64.urlsafe_b64decode(html_data).decode("utf-8")
                    body_data = BeautifulSoup(decoded_html, "html.parser").get_text()
                    break
    else:
        body_data = payload["body"].get("data")

    if not body_data:
        return None

    if not isinstance(body_data, str):
        body_data = base64.urlsafe_b64decode(body_data).decode("utf-8")
    return body_data.strip()

def summarize_email(subject):
    try:
        service = get_gmail_service()
        msg_id = search_email_by_subject(service, subject)
        if not msg_id:
            raise HTTPException(status_code=404, detail="No email found with given subject")
        
        body = get_email_body(service, msg_id)
        if not body:
            raise HTTPException(status_code=404, detail="Email has no readable body")
        summary = call_claude(f"Summarize the following email in a few sentences:\n\n{body}")
        print (summary)
        return f"✅ {summary}"
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def resolve_relative_dates(text):
    patterns = [
        r"\b(?:today|tomorrow|yesterday)\b",
        r"\b(?:this|next|coming)\s+(?:Monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(?:in\s+\d+\s+(?:day|days|week|weeks))\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print('MATCHED {}'.format(pattern))
            relative_phrase = match.group(0)
            parsed_date = dateparser.parse(relative_phrase, settings={"PREFER_DATES_FROM": "future"})
            if parsed_date:
                resolved = parsed_date.strftime("%Y-%m-%d")
                print(f"[resolve_relative_dates] Extracted: '{relative_phrase}' → {resolved}")
                return resolved

    print("[resolve_relative_dates] No match or parseable phrase found.")
    return None

def get_events_by_date(date="2025-08-04"):
    resp_dict = { "tool_name": "get_calendar_events","parameters": {"date": date} }
    return resp_dict

def schedule_meeting_llm(title, start_time, end_time, attendees=[], gmeet=False):
    # Dummy data for example – normally this would be parsed from LLM tool call
    response = {
        "tool_name": "schedule_meeting",
        "parameters": {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees,
            "create_meet_link": gmeet
        }
    }
    print ('response from schedule_meeting_llm {}'.format(response))
    return response

# === STEP 2: Define tool registry ===
tool_registry = {
    "add_numbers": add_numbers,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
    "get_weather": get_weather,
    "email_agent": email_agent,
    "mark_email": mark_email,
    "summarize_email": summarize_email,
    "get_events_by_date": get_events_by_date,
    "schedule_meeting_llm": schedule_meeting_llm,
    "analyze_document": analyze_document
}

# === STEP 3: Use LLM to parse the user's intent ===
# Note: Direct calls now use call_llm from claude_cli_client

# === STEP 4: Parse intent and execute tools manually ===
def process_input(user_query):
    print("\n[INFO] [process_input] Sending prompt to Claude...")

    resolved_date = resolve_relative_dates(user_query)
    today = datetime.now().strftime("%Y-%m-%d")

    if resolved_date:
        user_query += f" (The resolved date: {resolved_date})"  # <=== Inject into prompt
        print('user_query is {}'.format(user_query))

    system_prompt = (
        "You are an AI tool-calling assistant."
        " Read the user's query and return an output in JSON object in the format: {\"tool\": tool_name, \"args\": arguments}."
        "\nAvailable tools are:"
        " add_numbers(numbers: list of numbers) : returns the result of addition"
        " subtract(a: number, b: number) : returns the result of substraction"
        " multiply(numbers: list of numbers) : returns the result of multiplication"
        " divide(a: number, b: number) : returns the result of division"
        " get_weather(city: string) : returns the weather of the city passed as a parameter."
        " summarize_email(subject: string) : summarizes the email with a particular subject. Example of user input - Summarize the email with subject 'any particular subject'.Exclusively call this fucntion when user input mentions 'email summary' or 'summarize an emali' etc in user input"
        " analyze_document(path: string) : analyzes or summarizes a text or PDF document from the specified file path."
        f" get_events_by_date(date: string) : returns a json dict. Today is {today}. Interpret 'today', 'tomorrow' and all other dates based on {today}. The date parameter should be passed to the tool in YYYY-MM-DD format. If any resolved date is mentioned in parentheses like (Resolved date: 2025-08-09), consider using it as the 'date' parameter. User query can be like - Show the events for August 10, list the events for today, fetch the events for 31st May, Display meetings for next Friday."
        " email_agent(query: string) : sends email to the mentioned recipients with subject and body."
        " mark_email(mail_sub: string, mark_as_read: boolean) : marks an email with subject as read/unread. example user input - Mark the email with subject 'current quarter company highlights' as read."
        " schedule_meeting_llm(title : string, start_time : string, end_time : string, attendees : list of string, gmeet: bool). It returns meeting details dictionary with fields like title, start_time, end_time, attendees(optional), gmeet(optional).User input example 1 -  Set up a meeting called Project Update on 10 July from 10 AM to 11 AM. Here the parameters are title = Project Update, start_time = 2025-07-10T10:00:00 , end_time = 2025-07-10T10:00:00. Parameters attendees and gmeet are optional. User Input example 2 - Schedule a meeting called team sync on August 31st from 3 PM to 4 PM with attendees alice@example.com and bob@example.com including Meeting link. Here the parameters are title = team sync , start_time = 2025-08-31T15:00:00 , end_time = 2025-08-31T16:00:00, attendees = [\"alice@example.com\", \"bob@example.com\"] , gmeet = true ." 
        "\nIf there is no available tool for the respective user input, then just return { \"tool\": null, \"args\": { \"query\": \"...\" } }"
        "\nONLY return a valid JSON. No explanation, no markdown."
    )

    full_prompt = system_prompt + f"\nUser: {user_query}\n"
    output = call_llm(full_prompt)

    try:
        print(f"[DEBUG] Claude output: {output}")

        # Strip markdown code fences if present
        output = output.strip()
        if output.startswith("```"):
            # Remove opening fence (```json or ```)
            lines = output.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            output = "\n".join(lines).strip()

        tool_call = json.loads(output)
        tool_name = tool_call["tool"]
        args = tool_call["args"]

        if tool_name in tool_registry:
            result = tool_registry[tool_name](**args)
            print("✅ Tool {} returned: {}".format(tool_name, result))
            #return f"{result}"
            return result

        elif tool_name is None:
            # Fallback to direct LLM response
            print("[INFO] No tool used. Asking Claude directly for response...")
            response = call_llm(args.get("query", user_query))
            return f"{response}"

        else:
            return f"❌ Unknown tool: {tool_name}"

    except json.JSONDecodeError:
        return "❌ Invalid JSON from Claude. Falling back to chat mode:\n" + call_llm(user_query)

    except Exception as e:
        return f"❌ Error while executing tool: {e}"


# === CLI Entry Point ===
if __name__ == "__main__":
    print("🤖 Claude Tool Executor")
    while True:
        user_input = input("\n🧠 Your query (or 'exit'): ")
        if user_input.strip().lower() in ["exit", "quit"]:
            break
        result = process_input(user_input)
        if result:
            print(f"\n📤 Result: {result}")
    #print(summarize_email("unique test competition"))
