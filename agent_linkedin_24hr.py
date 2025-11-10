"""
UAE Nursing Jobs - LinkedIn 24-Hour Scraper
Daily comprehensive search - ONLY LinkedIn platform
"""

import os, hashlib, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
from jobspy import scrape_jobs
import gspread
from google.oauth2.service_account import Credentials

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

print("="*80)
print("🔵 LinkedIn Jobs - 24-Hour Daily Scraper")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================
SHEET_ID = os.getenv("SHEET_ID", "1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU")
CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")

# For 24-hour runs, search last 48 hours (2 days - fresh jobs only)
HOURS_OLD = 48  # Last 48 hours (2 days)
LINKEDIN_ONLY = ["linkedin"]

now = datetime.now()
start_date = now - timedelta(hours=HOURS_OLD)

print(f"⏰ Run time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🔍 Searching LinkedIn for jobs from last {HOURS_OLD} hours (48 hours / 2 days)")
print(f"📅 Time range: {start_date.strftime('%B %d, %Y %H:%M')} to {now.strftime('%B %d, %Y %H:%M')}")
print("="*80)

# ============================================================================
# STATUS TRACKING
# ============================================================================
run_status = {
    "start_time": datetime.now(),
    "searches_completed": 0,
    "total_jobs_scraped": 0,
    "new_jobs_added": 0,
    "errors": [],
    "success": False
}

def log_status(message, status_type="INFO"):
    """Log status with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    symbol = symbols.get(status_type, "ℹ️")
    print(f"[{timestamp}] {symbol} {message}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def uid_for(row) -> str:
    """Generate unique ID for deduplication"""
    if isinstance(row, dict):
        key = "|".join([
            str(row.get("Job Title","")).strip().lower(),
            str(row.get("Company Name","")).strip().lower(),
            str(row.get("Location","")).strip().lower(),
            str(row.get("Apply Link","")).strip().lower(),
        ])
    else:
        key = "|".join([
            str(row.get("Job Title") if hasattr(row, 'get') else row["Job Title"]).strip().lower(),
            str(row.get("Company Name") if hasattr(row, 'get') else row["Company Name"]).strip().lower(),
            str(row.get("Location") if hasattr(row, 'get') else row["Location"]).strip().lower(),
            str(row.get("Apply Link") if hasattr(row, 'get') else row["Apply Link"]).strip().lower(),
        ])
    return hashlib.md5(key.encode("utf-8")).hexdigest()

# ============================================================================
# LINKEDIN SCRAPING (Comprehensive 24-hour search)
# ============================================================================

log_status("Starting comprehensive LinkedIn job search...", "INFO")

all_jobs = []

try:
    # Search 1: Dubai nursing
    log_status("[1/5] Dubai nursing jobs (LinkedIn)...", "INFO")
    jobs1 = scrape_jobs(
        site_name=LINKEDIN_ONLY,
        search_term="nurse nursing registered nurse",
        location="Dubai",
        results_wanted=200,  # More results for daily comprehensive search
        hours_old=HOURS_OLD,
        country_indeed='United Arab Emirates'
    )
    all_jobs.append(jobs1)
    run_status["searches_completed"] += 1

    # Search 2: DHA licensed
    log_status("[2/5] DHA licensed nursing jobs (LinkedIn)...", "INFO")
    jobs2 = scrape_jobs(
        site_name=LINKEDIN_ONLY,
        search_term="DHA licensed nurse Dubai Health Authority",
        location="",
        results_wanted=200,
        hours_old=HOURS_OLD
    )
    all_jobs.append(jobs2)
    run_status["searches_completed"] += 1

    # Search 3: Abu Dhabi
    log_status("[3/5] Abu Dhabi nursing jobs (LinkedIn)...", "INFO")
    jobs3 = scrape_jobs(
        site_name=LINKEDIN_ONLY,
        search_term="nurse nursing healthcare",
        location="Abu Dhabi",
        results_wanted=200,
        hours_old=HOURS_OLD,
        country_indeed='United Arab Emirates'
    )
    all_jobs.append(jobs3)
    run_status["searches_completed"] += 1

    # Search 4: Sharjah
    log_status("[4/5] Sharjah nursing jobs (LinkedIn)...", "INFO")
    jobs4 = scrape_jobs(
        site_name=LINKEDIN_ONLY,
        search_term="nurse nursing RN staff nurse",
        location="Sharjah",
        results_wanted=150,
        hours_old=HOURS_OLD,
        country_indeed='United Arab Emirates'
    )
    all_jobs.append(jobs4)
    run_status["searches_completed"] += 1

    # Search 5: UAE-wide clinical positions
    log_status("[5/5] UAE clinical nursing positions (LinkedIn)...", "INFO")
    jobs5 = scrape_jobs(
        site_name=LINKEDIN_ONLY,
        search_term="clinical nurse practitioner healthcare UAE",
        location="United Arab Emirates",
        results_wanted=150,
        hours_old=HOURS_OLD
    )
    all_jobs.append(jobs5)
    run_status["searches_completed"] += 1

    log_status(f"LinkedIn searches completed: {run_status['searches_completed']}/5", "SUCCESS")

except Exception as e:
    log_status(f"LinkedIn scraping error: {e}", "ERROR")
    run_status["errors"].append(str(e))
    all_jobs = []

# ============================================================================
# PROCESS RESULTS
# ============================================================================

if all_jobs:
    log_status("Processing scraped jobs...", "INFO")

    jobs_df = pd.concat(all_jobs, ignore_index=True)
    jobs_df = jobs_df.drop_duplicates(subset=['job_url'], keep='first')

    run_status["total_jobs_scraped"] = len(jobs_df)
    log_status(f"Total unique jobs scraped: {len(jobs_df)}", "SUCCESS")

    new_jobs = []
    for _, row in jobs_df.iterrows():
        new_jobs.append({
            "Job Title": row['title'],
            "Company Name": row['company'],
            "Location": row['location'],
            "Apply Link": row['job_url'],
            "Source": f"{row['site'].capitalize()} (24hr)",
            "Collected At": now_iso(),
            "Description": row.get('description', ''),
            "_uid": ""
        })

    new_jobs_df = pd.DataFrame(new_jobs)

    # Generate UIDs
    new_jobs_df["_uid"] = new_jobs_df.apply(uid_for, axis=1)

    log_status(f"Prepared {len(new_jobs_df)} jobs for upload", "INFO")

else:
    log_status("No jobs scraped", "WARNING")
    new_jobs_df = pd.DataFrame()

# ============================================================================
# GOOGLE SHEETS - ADD NEW JOBS ONLY
# ============================================================================

log_status("Connecting to Google Sheets...", "INFO")

try:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet = spreadsheet.sheet1

    log_status("Connected to Google Sheets", "SUCCESS")

    # Load existing data
    log_status("Loading existing jobs from sheet...", "INFO")
    existing_data = worksheet.get_all_values()

    if len(existing_data) > 1:
        headers = existing_data[0]
        existing_df = pd.DataFrame(existing_data[1:], columns=headers)
        log_status(f"Found {len(existing_df)} existing jobs in sheet", "INFO")
    else:
        existing_df = pd.DataFrame()
        log_status("Sheet is empty, will create new sheet", "INFO")

    # Filter for separator rows and job rows
    if not existing_df.empty and "_uid" in existing_df.columns:
        separator_mask = existing_df["_uid"].str.strip() == ""
        job_rows_df = existing_df[~separator_mask].copy()
        separator_rows = existing_df[separator_mask].copy()
        existing_uids = set(job_rows_df["_uid"].dropna())
        log_status(f"Existing unique job UIDs: {len(existing_uids)}", "INFO")
    else:
        job_rows_df = pd.DataFrame()
        separator_rows = pd.DataFrame()
        existing_uids = set()

    # Filter NEW jobs only
    if not new_jobs_df.empty and not existing_uids:
        truly_new = new_jobs_df.copy()
    elif not new_jobs_df.empty:
        truly_new = new_jobs_df[~new_jobs_df["_uid"].isin(existing_uids)].copy()
    else:
        truly_new = pd.DataFrame()

    new_jobs_count = len(truly_new)
    run_status["new_jobs_added"] = new_jobs_count

    if new_jobs_count > 0:
        log_status(f"🔥 Found {new_jobs_count} NEW LinkedIn jobs to add!", "SUCCESS")

        # SIMPLE APPEND MODE - Just add new jobs to existing data
        # Convert timestamps to string
        truly_new["Collected At"] = pd.to_datetime(truly_new["Collected At"], errors='coerce').astype(str)

        # Append new jobs at the END of existing data (will appear at bottom)
        log_status("Appending new jobs to sheet...", "INFO")

        # Get current sheet row count
        existing_row_count = len(existing_data)
        start_row = existing_row_count + 1

        # Convert to list format for append
        new_rows = truly_new.values.tolist()

        # Append rows (no formatting, no separators - keeps existing sheet clean)
        worksheet.append_rows(new_rows, value_input_option='RAW')

        log_status(f"✅ Appended {new_jobs_count} new LinkedIn jobs to sheet!", "SUCCESS")

    else:
        log_status("No new LinkedIn jobs found in last 7 days", "INFO")

    run_status["success"] = True
    run_status["total_jobs_in_sheet"] = len(job_rows_df) + new_jobs_count

except Exception as e:
    log_status(f"Google Sheets error: {e}", "ERROR")
    run_status["errors"].append(str(e))
    run_status["total_jobs_in_sheet"] = len(job_rows_df) if 'job_rows_df' in locals() else 0
    import traceback
    traceback.print_exc()

# ============================================================================
# FINAL STATUS SUMMARY
# ============================================================================

end_time = datetime.now()
duration = (end_time - run_status["start_time"]).total_seconds()

print("\n" + "="*80)
print("📊 LINKEDIN 24-HOUR SCRAPER - RUN SUMMARY")
print("="*80)
log_status(f"Total runtime: {int(duration)} seconds ({duration/60:.1f} minutes)", "INFO")
log_status(f"LinkedIn searches: {run_status['searches_completed']}/5 completed", "SUCCESS")
log_status(f"Jobs scraped this run: {run_status['total_jobs_scraped']}", "SUCCESS")
log_status(f"🔥 NEW jobs added to sheet: {run_status['new_jobs_added']}", "SUCCESS")
log_status(f"📝 Total jobs in sheet: {run_status['total_jobs_in_sheet']}", "SUCCESS")

if run_status["errors"]:
    log_status(f"Errors encountered: {len(run_status['errors'])}", "ERROR")
    for i, err in enumerate(run_status["errors"], 1):
        print(f"  {i}. {err}")

if run_status["success"]:
    log_status("Agent completed successfully! ✅", "SUCCESS")
else:
    log_status("Agent completed with errors ⚠️", "WARNING")

print("="*80)
print(f"🏁 Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
