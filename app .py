import streamlit as st
import feedparser
import pandas as pd
import requests
import re
import html
import smtplib
import json
from datetime import datetime, timezone
from email.message import EmailMessage
from urllib.parse import quote_plus

st.set_page_config(page_title="News Research AI Agent", page_icon="📰", layout="wide")

st.markdown("""
<style>
.main {background: linear-gradient(180deg, rgba(40,80,150,.05), transparent 260px);}
.hero {padding: 1.4rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg,#102a43,#2463a6); color:white; margin-bottom:1rem;}
.hero h1 {color:white; margin:0;} .hero p {color:#e8f1ff; margin:.4rem 0 0 0;}
div[data-testid="stMetric"] {background:rgba(100,130,180,.09);padding:14px;border-radius:12px;}
</style>
<div class="hero"><h1>📰 News Research AI Agent</h1><p>Search current news • Summarize • Save to Google Sheets • Draft and email a professional briefing</p></div>
""", unsafe_allow_html=True)

st.caption("API-key-free research mode: searches Google News RSS. No Groq/OpenAI key is used. Cloud storage and sending email require your own authorized credentials.")

with st.sidebar:
    st.header("⚙️ Research settings")
    topic = st.text_input("News topic", "Artificial Intelligence")
    count = st.slider("Maximum stories", 3, 15, 5)
    language = st.selectbox("News language", ["English", "Urdu"], index=0)
    period = st.selectbox("Time range", ["Past hour", "Past 24 hours", "Past week", "Any time"], index=2)
    region = st.selectbox("Region", ["Worldwide", "Pakistan", "United States", "United Kingdom", "India"], index=0)
    search_btn = st.button("🔎 Research latest news", type="primary", use_container_width=True)

REGION = {
    "Worldwide": ("US", "US:en"), "Pakistan": ("PK", "PK:en"),
    "United States": ("US", "US:en"), "United Kingdom": ("GB", "GB:en"), "India": ("IN", "IN:en")
}


def clean_text(value):
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def summarize(text, max_chars=420):
    """Create a short, readable summary from the publisher's RSS description; no LLM/API required."""
    text = clean_text(text)
    if not text:
        return "No article description was provided in the news feed. Open the reference link for the full report."
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result = " ".join(sentences[:3]).strip()
    if len(result) > max_chars:
        result = result[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"
    return result


def fetch_news(topic, count, language, period, region):
    gl, ceid = REGION[region]
    hl = "ur" if language == "Urdu" else "en-US"
    q = topic
    if period != "Any time":
        q += {"Past hour": " when:1h", "Past 24 hours": " when:1d", "Past week": " when:7d"}[period]
    url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={hl}&gl={gl}&ceid={ceid}"
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 NewsResearchAgent/1.0"})
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    rows, seen = [], set()
    for entry in feed.entries:
        title = clean_text(getattr(entry, "title", ""))
        link = getattr(entry, "link", "")
        if not title or not link or link in seen:
            continue
        seen.add(link)
        published = getattr(entry, "published", "")
        source = ""
        if getattr(entry, "source", None):
            source = clean_text(entry.source.get("title", ""))
        desc = getattr(entry, "summary", "")
        rows.append({
            "Title": title,
            "Summary": summarize(desc),
            "Reference": link,
            "Date": published,
            "Source": source,
            "Topic": topic,
        })
        if len(rows) >= count:
            break
    return pd.DataFrame(rows, columns=["Title", "Summary", "Reference", "Date", "Source", "Topic"])


def get_gspread_client(service_account_json):
    import gspread
    from google.oauth2.service_account import Credentials
    info = json.loads(service_account_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


def save_to_sheet(df, service_account_json, spreadsheet_url, worksheet_name):
    client = get_gspread_client(service_account_json)
    book = client.open_by_url(spreadsheet_url)
    try:
        ws = book.worksheet(worksheet_name)
    except Exception:
        ws = book.add_worksheet(title=worksheet_name, rows="1000", cols="6")
    headers = ["Title", "Summary", "Reference", "Date", "Source", "Topic"]
    existing = ws.get_all_values()
    if not existing:
        ws.append_row(headers, value_input_option="USER_ENTERED")
        existing_refs = set()
    else:
        if existing[0] != headers:
            # Preserve existing sheet contents and use the first row as headers only when blank.
            raise ValueError(f"Worksheet '{worksheet_name}' already has different headers. Use a blank worksheet or rename it.")
        existing_refs = {row[2] for row in existing[1:] if len(row) >= 3 and row[2]}
    new_rows = []
    for _, row in df.iterrows():
        if row["Reference"] not in existing_refs:
            new_rows.append([str(row[c]) for c in headers])
    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")
    return len(new_rows), book.url


def make_email(topic, df, recipient_name, sender_name, sheet_url=""):
    today = datetime.now().strftime("%d %B %Y")
    lines = [f"Dear {recipient_name or 'Sir/Madam'},", "", "I hope this message finds you well.",
             f"Please find below a brief update on the latest news regarding {topic}, researched on {today}.", ""]
    for i, (_, row) in enumerate(df.head(10).iterrows(), 1):
        lines += [f"{i}. {row['Title']}", str(row['Summary']), f"Reference: {row['Reference']}", ""]
    if sheet_url:
        lines += [f"The complete news list is available in the Google Sheet: {sheet_url}", ""]
    lines += ["Please let me know if you would like further details on any of these developments.", "", "Kind regards,", sender_name or "News Research Team"]
    return f"Daily News Update — {topic} | {today}", "\n".join(lines)


def send_email_smtp(sender_email, app_password, recipient_email, subject, body, cc_email=""):
    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    if cc_email.strip():
        msg["Cc"] = cc_email.strip()
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=25) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)

if "news_df" not in st.session_state:
    st.session_state.news_df = pd.DataFrame(columns=["Title", "Summary", "Reference", "Date", "Source", "Topic"])
if "sheet_url" not in st.session_state:
    st.session_state.sheet_url = ""

if search_btn:
    if not topic.strip():
        st.error("Please enter a news topic first.")
    else:
        with st.spinner(f"Searching Google News for: {topic} …"):
            try:
                df = fetch_news(topic.strip(), count, language, period, region)
                st.session_state.news_df = df
                if df.empty:
                    st.warning("No matching stories were returned. Try a broader topic or time range.")
                else:
                    st.success(f"Found {len(df)} stories. Review the results before saving or emailing.")
            except requests.RequestException as exc:
                st.error(f"Could not reach Google News RSS. Check your internet connection and try again. Details: {exc}")
            except Exception as exc:
                st.error(f"Research failed: {exc}")

df = st.session_state.news_df
if not df.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("Stories found", len(df))
    c2.metric("Unique reference links", df["Reference"].nunique())
    c3.metric("Research topic", str(df.iloc[0]["Topic"]))
    st.subheader("📋 Research results")
    st.dataframe(df[["Title", "Summary", "Reference", "Date", "Source", "Topic"]], use_container_width=True, hide_index=True,
                 column_config={"Reference": st.column_config.LinkColumn("Reference", display_text="Open article")})
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download news as CSV", data=csv, file_name=f"news_{re.sub(r'[^a-zA-Z0-9]+','_',str(df.iloc[0]['Topic'])).strip('_')}.csv", mime="text/csv")

    st.divider()
    st.subheader("📊 Save to Google Sheets")
    st.info("One-time setup: create a Google Cloud service account, enable Google Sheets API and Google Drive API, download its JSON key, then share your target Google Sheet with the service-account email as Editor. Paste the JSON below only in a trusted/private session; do not commit it to GitHub.")
    with st.expander("Google Sheets connection", expanded=False):
        service_json = st.text_area("Service account JSON", height=140, placeholder='Paste the full contents of your service-account JSON key file')
        sheet_url = st.text_input("Google Spreadsheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")
        worksheet = st.text_input("Worksheet/tab name", "News")
        if st.button("💾 Append new stories to Google Sheet", type="primary"):
            if not service_json.strip() or not sheet_url.strip():
                st.warning("Please provide the service-account JSON and spreadsheet URL.")
            else:
                try:
                    added, actual_url = save_to_sheet(df, service_json, sheet_url, worksheet.strip() or "News")
                    st.session_state.sheet_url = actual_url
                    st.success(f"Google Sheet updated. Added {added} new row(s); duplicate reference links were skipped.")
                    st.link_button("Open Google Sheet", actual_url)
                except Exception as exc:
                    st.error(f"Google Sheets save failed: {exc}")

    st.divider()
    st.subheader("✉️ Formal email to your boss")
    with st.expander("Email settings and preview", expanded=True):
        a, b = st.columns(2)
        with a:
            recipient_name = st.text_input("Boss / recipient name", "Sir/Madam")
            recipient_email = st.text_input("Recipient email address")
            cc_email = st.text_input("CC (optional)")
        with b:
            sender_name = st.text_input("Your name", "News Research Team")
            sender_email = st.text_input("Your Gmail address")
            app_password = st.text_input("Gmail App Password", type="password", help="Use a Google App Password with 2-Step Verification enabled. Do not use your normal Gmail password.")
        subject, body = make_email(str(df.iloc[0]["Topic"]), df, recipient_name, sender_name, st.session_state.sheet_url)
        st.markdown("**Email subject**")
        st.code(subject)
        st.markdown("**Email body preview**")
        st.text_area("Review the email before sending", body, height=260, key="email_preview")
        confirm_send = st.checkbox("I reviewed the email and confirm that it should be sent.")
        if st.button("📨 Send formal email", type="primary"):
            if not confirm_send:
                st.warning("Please confirm after reviewing the email.")
            elif not all([recipient_email.strip(), sender_email.strip(), app_password.strip()]):
                st.warning("Please enter the recipient email, sender Gmail address and Gmail App Password.")
            else:
                try:
                    send_email_smtp(sender_email.strip(), app_password.strip(), recipient_email.strip(), subject, st.session_state.email_preview, cc_email)
                    st.success(f"Email sent to {recipient_email.strip()}.")
                except Exception as exc:
                    st.error(f"Email could not be sent: {exc}. Check your Gmail address, App Password and account security settings.")
else:
    st.markdown("### 🚀 Start here")
    st.write("1. Enter any topic in the sidebar.\n2. Click **Research latest news**.\n3. Review the stories and download a CSV if needed.\n4. Connect Google Sheets to append rows without duplicates.\n5. Review the formal email and explicitly confirm before sending.")
    st.warning("This version uses the news publisher's RSS description for short summaries. Some feeds may provide only a short snippet; open the reference link for the full article.")

with st.expander("🔐 Security and deployment notes"):
    st.markdown("""
- Never upload service-account JSON files, Gmail App Passwords, or other secrets to a public GitHub repository.
- The app does not use Groq, OpenAI, or any paid LLM API. It does require an internet connection for live news.
- Google Sheets requires Google Cloud API setup and permission to edit the target sheet.
- Gmail sending requires a Gmail App Password (with 2-Step Verification enabled) or a separately configured mail service.
- Streamlit Community Cloud apps are public by default unless access controls are configured. Avoid pasting credentials into a shared/public session.
- This app is manually triggered; scheduled daily runs require a scheduler/automation service.
""")
