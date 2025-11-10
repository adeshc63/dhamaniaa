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

# For 24-hour runs, search last 7 days (to catch jobs posted on weekends)
HOURS_OLD = 168  # Last 7 days
LINKEDIN_ONLY = ["linkedin"]

now = datetime.now()
start_date = now - timedelta(hours=HOURS_OLD)

print(f"⏰ Run time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🔍 Searching LinkedIn for jobs from last {HOURS_OLD} hours (7 days)")
print(f"📅 Time range: {start_date.strftime('%B %d, %Y')} to {now.strftime('%B %d, %Y')}")
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

        # Combine: new jobs + existing jobs
        combined_df = pd.concat([truly_new, job_rows_df], ignore_index=True)

        # Sort by date (newest first)
        combined_df["Collected At"] = pd.to_datetime(combined_df["Collected At"], errors='coerce')
        combined_df = combined_df.sort_values(by="Collected At", ascending=False, na_position='last')

        # Convert Timestamp to string for JSON serialization
        combined_df["Collected At"] = combined_df["Collected At"].astype(str)

        log_status(f"Total jobs after adding new: {len(combined_df)}", "INFO")

        # Prepare data with DAILY separators
        log_status("Adding daily date separators...", "INFO")

        data_to_upload = [list(combined_df.columns)]

        current_month = None
        current_date = None
        date_separator_rows = []
        month_separator_rows = []

        for idx, row in combined_df.iterrows():
            try:
                collected_date = pd.to_datetime(row['Collected At'])
                year_num = collected_date.year
                month_num = collected_date.month
                day_num = collected_date.day
                month_key = f"{year_num}-{month_num:02d}"
                date_key = f"{year_num}-{month_num:02d}-{day_num:02d}"

                # Add month separator if month changed
                if current_month != month_key:
                    current_month = month_key
                    month_label = f"═══════════ {collected_date.strftime('%B %Y').upper()} ═══════════"
                    month_row = [month_label] + [''] * (len(combined_df.columns) - 1)
                    data_to_upload.append(month_row)
                    month_separator_rows.append(len(data_to_upload))
                    current_date = None

                # Add DAILY separator if date changed
                if current_date != date_key:
                    current_date = date_key
                    date_label = f"📅 {collected_date.strftime('%A, %B %d, %Y')}"
                    date_row = [date_label] + [''] * (len(combined_df.columns) - 1)
                    data_to_upload.append(date_row)
                    date_separator_rows.append(len(data_to_upload))
            except:
                pass

            data_to_upload.append(row.tolist())

        # Upload to Google Sheets
        log_status("Uploading to Google Sheets...", "INFO")
        worksheet.clear()
        worksheet.update(data_to_upload, value_input_option='RAW')

        # Format separators
        log_status("Applying formatting to separators...", "INFO")

        # Green background for month separators
        for row_num in month_separator_rows:
            worksheet.format(f"A{row_num}:Z{row_num}", {
                "backgroundColor": {"red": 0.8, "green": 1.0, "blue": 0.8},
                "textFormat": {"bold": True, "fontSize": 12},
                "horizontalAlignment": "CENTER"
            })

        # Blue background for daily separators
        for row_num in date_separator_rows:
            worksheet.format(f"A{row_num}:Z{row_num}", {
                "backgroundColor": {"red": 0.8, "green": 0.9, "blue": 1.0},
                "textFormat": {"bold": True, "fontSize": 11},
                "horizontalAlignment": "LEFT"
            })

        log_status("✅ Sheet updated successfully with daily separators!", "SUCCESS")

    else:
        log_status("No new LinkedIn jobs found in last 7 days", "INFO")

    run_status["success"] = True
    run_status["total_jobs_in_sheet"] = len(combined_df) if 'combined_df' in locals() and new_jobs_count > 0 else len(job_rows_df)

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
