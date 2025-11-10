"""
UAE Nursing Jobs Agent - GitHub Actions Automation
Hourly updates - NEW jobs ADDED, old jobs KEPT
Latest jobs always on top
"""

import os, hashlib, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
from jobspy import scrape_jobs
import gspread
from google.oauth2.service_account import Credentials
import requests
from bs4 import BeautifulSoup

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

print("="*80)
print("Starting JobSpy - Nursing & DHA Jobs Scraper -> Google Sheets")
print("Hourly Update Mode - Add New Jobs Only")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================
SHEET_ID = os.getenv("SHEET_ID", "1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU")
CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")

# Search for last 30 days (720 hours) to ensure we get all recent jobs
from datetime import datetime as dt
now = dt.now()

HOURS_OLD = 720  # Last 30 days
ALL_PLATFORMS = ["indeed", "linkedin"]  # Naukri removed - blocked by recaptcha

# Calculate the start date for display
from datetime import timedelta
start_date = now - timedelta(hours=HOURS_OLD)

print(f"Searching for jobs from: {start_date.strftime('%B %d, %Y')} to {now.strftime('%B %d, %Y')}")
print(f"Hours to search: {HOURS_OLD} hours (last 30 days)")
print(f"🕐 Agent started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# ============================================================================
# STATUS TRACKING
# ============================================================================
run_status = {
    "start_time": datetime.now(),
    "jobspy_searches_completed": 0,
    "hospital_scrapers_completed": 0,
    "total_jobs_scraped": 0,
    "new_jobs_added": 0,
    "total_jobs_in_sheet": 0,
    "errors": [],
    "success": False
}

def log_status(message, status_type="INFO"):
    """Log status with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    symbol = symbols.get(status_type, "ℹ️")
    print(f"[{timestamp}] {symbol} {message}")

log_status("Agent initialization complete", "SUCCESS")

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

def scrape_greenhouse_jobs(api_url, company_name, location_filter=""):
    """Scrape jobs from Greenhouse API"""
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code != 200:
            return []

        data = response.json()
        jobs = data.get('jobs', [])

        hospital_jobs = []
        for job in jobs:
            title = job.get('title', '').lower()
            location = job.get('location', {}).get('name', '') if isinstance(job.get('location'), dict) else str(job.get('location', ''))

            # Filter for nursing jobs
            if any(keyword in title for keyword in ['nurse', 'nursing', 'rn', 'registered nurse', 'staff nurse', 'clinical']):
                # Filter by location if specified
                if location_filter and location_filter.lower() not in location.lower():
                    continue

                hospital_jobs.append({
                    'Job Title': job.get('title', ''),
                    'Platform': company_name,
                    'Company Name': company_name,
                    'Description': job.get('content', '')[:500],
                    'Location': location,
                    'Work Model': '',
                    'Published': now_iso().split('T')[0],
                    'Salary': '',
                    'Seniority': '',
                    'Company Size': '',
                    'Industry': 'Healthcare',
                    'Apply Link': job.get('absolute_url', ''),
                    'Source': f'{company_name} (Direct)',
                    'Collected At': now_iso(),
                    '_uid': ''
                })

        return hospital_jobs
    except Exception as e:
        print(f"Error scraping {company_name}: {e}")
        return []

def scrape_nmc_healthcare():
    """Scrape NMC Healthcare careers via Greenhouse"""
    print("\n[Hospital 1/6] Scraping NMC Healthcare...")
    jobs = scrape_greenhouse_jobs(
        "https://boards-api.greenhouse.io/v1/boards/nmchealthcare/jobs",
        "NMC Healthcare",
        location_filter="UAE"
    )
    print(f"Found {len(jobs)} nursing jobs from NMC Healthcare")
    return jobs

def scrape_kings_college():
    """Scrape Kings College Hospital Dubai"""
    print("\n[Hospital 2/6] Scraping Kings College Hospital...")
    jobs = scrape_greenhouse_jobs(
        "https://boards-api.greenhouse.io/v1/boards/kingscollegehospitaldubai/jobs",
        "Kings College Hospital Dubai",
        location_filter="Dubai"
    )
    print(f"Found {len(jobs)} nursing jobs from Kings College")
    return jobs

def scrape_burjeel_holdings():
    """Scrape Burjeel Holdings careers"""
    print("\n[Hospital 3/6] Scraping Burjeel Holdings...")
    try:
        url = "https://burjeelholdings.com/careers/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print("Could not access Burjeel careers page")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []

        # Look for job listings (adjust selectors based on actual page structure)
        job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career|position', re.I))

        for job_elem in job_elements[:20]:  # Limit to 20 jobs
            title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|job', re.I))
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)

            # Filter for nursing jobs
            if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn', 'registered nurse']):
                link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                apply_link = link_elem.get('href', url) if link_elem else url

                if not apply_link.startswith('http'):
                    apply_link = 'https://burjeelholdings.com' + apply_link

                jobs.append({
                    'Job Title': title,
                    'Platform': 'Burjeel Holdings',
                    'Company Name': 'Burjeel Holdings',
                    'Description': '',
                    'Location': 'UAE',
                    'Work Model': '',
                    'Published': now_iso().split('T')[0],
                    'Salary': '',
                    'Seniority': '',
                    'Company Size': '',
                    'Industry': 'Healthcare',
                    'Apply Link': apply_link,
                    'Source': 'Burjeel Holdings (Direct)',
                    'Collected At': now_iso(),
                    '_uid': ''
                })

        print(f"Found {len(jobs)} nursing jobs from Burjeel")
        return jobs
    except Exception as e:
        print(f"Error scraping Burjeel: {e}")
        return []

def scrape_mediclinic():
    """Scrape Mediclinic Middle East careers"""
    print("\n[Hospital 4/6] Scraping Mediclinic Middle East...")
    try:
        # Mediclinic uses Workday - try to access their careers API
        url = "https://mediclinic.wd3.myworkdayjobs.com/wday/cxs/mediclinic/Mediclinic_Middle_East/jobs"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": "nurse"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            data = response.json()
            job_postings = data.get('jobPostings', [])

            for job in job_postings:
                title_obj = job.get('title', '')
                title = title_obj if isinstance(title_obj, str) else ''

                jobs.append({
                    'Job Title': title,
                    'Platform': 'Mediclinic',
                    'Company Name': 'Mediclinic Middle East',
                    'Description': '',
                    'Location': job.get('locationsText', 'UAE'),
                    'Work Model': '',
                    'Published': now_iso().split('T')[0],
                    'Salary': '',
                    'Seniority': '',
                    'Company Size': '',
                    'Industry': 'Healthcare',
                    'Apply Link': f"https://mediclinic.wd3.myworkdayjobs.com/Mediclinic_Middle_East{job.get('externalPath', '')}",
                    'Source': 'Mediclinic (Direct)',
                    'Collected At': now_iso(),
                    '_uid': ''
                })

        print(f"Found {len(jobs)} nursing jobs from Mediclinic")
        return jobs
    except Exception as e:
        print(f"Error scraping Mediclinic: {e}")
        return []

def scrape_cleveland_clinic():
    """Scrape Cleveland Clinic Abu Dhabi"""
    print("\n[Hospital 5/6] Scraping Cleveland Clinic Abu Dhabi...")
    try:
        # Cleveland Clinic also uses Workday
        url = "https://clevelandclinic.wd5.myworkdayjobs.com/wday/cxs/clevelandclinic/AbuDhabi/jobs"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": "nurse"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            data = response.json()
            job_postings = data.get('jobPostings', [])

            for job in job_postings:
                title_obj = job.get('title', '')
                title = title_obj if isinstance(title_obj, str) else ''

                jobs.append({
                    'Job Title': title,
                    'Platform': 'Cleveland Clinic',
                    'Company Name': 'Cleveland Clinic Abu Dhabi',
                    'Description': '',
                    'Location': job.get('locationsText', 'Abu Dhabi'),
                    'Work Model': '',
                    'Published': now_iso().split('T')[0],
                    'Salary': '',
                    'Seniority': '',
                    'Company Size': '',
                    'Industry': 'Healthcare',
                    'Apply Link': f"https://clevelandclinic.wd5.myworkdayjobs.com/AbuDhabi{job.get('externalPath', '')}",
                    'Source': 'Cleveland Clinic (Direct)',
                    'Collected At': now_iso(),
                    '_uid': ''
                })

        print(f"Found {len(jobs)} nursing jobs from Cleveland Clinic")
        return jobs
    except Exception as e:
        print(f"Error scraping Cleveland Clinic: {e}")
        return []

def scrape_aster_dm():
    """Scrape Aster DM Healthcare"""
    print("\n[Hospital 6/15] Scraping Aster DM Healthcare...")
    try:
        url = "https://www.asterdmhealthcare.com/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print("Could not access Aster careers page")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []

        job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career|vacancy', re.I))

        for job_elem in job_elements[:20]:
            title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)

            if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                apply_link = link_elem.get('href', url) if link_elem else url

                if not apply_link.startswith('http'):
                    apply_link = 'https://www.asterdmhealthcare.com' + apply_link

                jobs.append({
                    'Job Title': title,
                    'Platform': 'Aster DM Healthcare',
                    'Company Name': 'Aster DM Healthcare',
                    'Description': '',
                    'Location': 'UAE',
                    'Work Model': '',
                    'Published': now_iso().split('T')[0],
                    'Salary': '',
                    'Seniority': '',
                    'Company Size': '',
                    'Industry': 'Healthcare',
                    'Apply Link': apply_link,
                    'Source': 'Aster DM (Direct)',
                    'Collected At': now_iso(),
                    '_uid': ''
                })

        print(f"Found {len(jobs)} nursing jobs from Aster")
        return jobs
    except Exception as e:
        print(f"Error scraping Aster: {e}")
        return []

def scrape_saudi_german():
    """Scrape Saudi German Hospital"""
    print("\n[Hospital 7/15] Scraping Saudi German Hospital...")
    try:
        url = "https://www.sghgroup.ae/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career|position', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.sghgroup.ae' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'Saudi German Hospital',
                        'Company Name': 'Saudi German Hospital',
                        'Description': '',
                        'Location': 'UAE',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'Saudi German (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from Saudi German")
        return jobs
    except Exception as e:
        print(f"Error scraping Saudi German: {e}")
        return []

def scrape_thumbay():
    """Scrape Thumbay Group"""
    print("\n[Hospital 8/15] Scraping Thumbay Group...")
    jobs = scrape_greenhouse_jobs(
        "https://boards-api.greenhouse.io/v1/boards/thumbaygroup/jobs",
        "Thumbay Group",
        location_filter="UAE"
    )
    print(f"Found {len(jobs)} nursing jobs from Thumbay")
    return jobs

def scrape_american_hospital_dubai():
    """Scrape American Hospital Dubai"""
    print("\n[Hospital 9/15] Scraping American Hospital Dubai...")
    try:
        url = "https://www.ahdubai.com/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.ahdubai.com' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'American Hospital Dubai',
                        'Company Name': 'American Hospital Dubai',
                        'Description': '',
                        'Location': 'Dubai',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'American Hospital (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from American Hospital")
        return jobs
    except Exception as e:
        print(f"Error scraping American Hospital: {e}")
        return []

def scrape_al_zahra():
    """Scrape Al Zahra Hospital"""
    print("\n[Hospital 10/15] Scraping Al Zahra Hospital...")
    try:
        url = "https://www.alzahra.com/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.alzahra.com' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'Al Zahra Hospital',
                        'Company Name': 'Al Zahra Hospital',
                        'Description': '',
                        'Location': 'Dubai',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'Al Zahra (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from Al Zahra")
        return jobs
    except Exception as e:
        print(f"Error scraping Al Zahra: {e}")
        return []

def scrape_zulekha():
    """Scrape Zulekha Hospital"""
    print("\n[Hospital 11/15] Scraping Zulekha Hospital...")
    try:
        url = "https://www.zulekhahospitals.com/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.zulekhahospitals.com' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'Zulekha Hospital',
                        'Company Name': 'Zulekha Hospital',
                        'Description': '',
                        'Location': 'UAE',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'Zulekha (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from Zulekha")
        return jobs
    except Exception as e:
        print(f"Error scraping Zulekha: {e}")
        return []

def scrape_fakeeh():
    """Scrape Dr. Sulaiman Al Habib (Fakeeh)"""
    print("\n[Hospital 12/15] Scraping Dr. Sulaiman Al Habib...")
    try:
        url = "https://www.drsulaimanalhabib.com/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.drsulaimanalhabib.com' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'Dr. Sulaiman Al Habib',
                        'Company Name': 'Dr. Sulaiman Al Habib',
                        'Description': '',
                        'Location': 'UAE',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'Dr. Sulaiman Al Habib (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from Dr. Sulaiman Al Habib")
        return jobs
    except Exception as e:
        print(f"Error scraping Dr. Sulaiman Al Habib: {e}")
        return []

def scrape_emirates_hospital():
    """Scrape Emirates Hospital"""
    print("\n[Hospital 13/15] Scraping Emirates Hospital...")
    try:
        url = "https://www.emirateshospital.ae/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.emirateshospital.ae' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'Emirates Hospital',
                        'Company Name': 'Emirates Hospital',
                        'Description': '',
                        'Location': 'UAE',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'Emirates Hospital (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from Emirates Hospital")
        return jobs
    except Exception as e:
        print(f"Error scraping Emirates Hospital: {e}")
        return []

def scrape_rak_hospital():
    """Scrape RAK Hospital"""
    print("\n[Hospital 14/15] Scraping RAK Hospital...")
    try:
        url = "https://www.rakhospital.com/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.rakhospital.com' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'RAK Hospital',
                        'Company Name': 'RAK Hospital',
                        'Description': '',
                        'Location': 'Ras Al Khaimah',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'RAK Hospital (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from RAK Hospital")
        return jobs
    except Exception as e:
        print(f"Error scraping RAK Hospital: {e}")
        return []

def scrape_healthpoint():
    """Scrape Healthpoint Hospital"""
    print("\n[Hospital 15/15] Scraping Healthpoint Hospital...")
    try:
        url = "https://www.healthpointhospital.com/careers"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)

        jobs = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|career', re.I))

            for job_elem in job_elements[:20]:
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if any(keyword in title.lower() for keyword in ['nurse', 'nursing', 'rn']):
                    link_elem = job_elem.find('a', href=True) or title_elem if title_elem.name == 'a' else None
                    apply_link = link_elem.get('href', url) if link_elem else url

                    if not apply_link.startswith('http'):
                        apply_link = 'https://www.healthpointhospital.com' + apply_link

                    jobs.append({
                        'Job Title': title,
                        'Platform': 'Healthpoint Hospital',
                        'Company Name': 'Healthpoint Hospital',
                        'Description': '',
                        'Location': 'Abu Dhabi',
                        'Work Model': '',
                        'Published': now_iso().split('T')[0],
                        'Salary': '',
                        'Seniority': '',
                        'Company Size': '',
                        'Industry': 'Healthcare',
                        'Apply Link': apply_link,
                        'Source': 'Healthpoint (Direct)',
                        'Collected At': now_iso(),
                        '_uid': ''
                    })

        print(f"Found {len(jobs)} nursing jobs from Healthpoint")
        return jobs
    except Exception as e:
        print(f"Error scraping Healthpoint: {e}")
        return []

# ============================================================================
# JOBSPY SCRAPING
# ============================================================================

log_status("Starting JobSpy scraping (7 searches)", "INFO")
all_jobs = []
total_before_dedup = 0

# Search 1: General nursing jobs in Dubai
print(f"\n[1/7] Searching for nursing jobs in Dubai (Last 30 days - {HOURS_OLD} hours)...")
log_status("JobSpy Search 1/7: Dubai nursing jobs", "INFO")
jobs1 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="nurse nursing registered nurse",
    location="Dubai",
    results_wanted=150,
    hours_old=HOURS_OLD,
    country_indeed='United Arab Emirates'
)
all_jobs.append(jobs1)
total_before_dedup += len(jobs1)
print(f"Found {len(jobs1)} jobs")

# Search 2: DHA licensed nursing jobs - WORLDWIDE
print(f"\n[2/7] Searching for DHA licensed nursing jobs WORLDWIDE (Last 30 days - {HOURS_OLD} hours)...")
jobs2 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="DHA licensed nurse Dubai Health Authority",
    location="",
    results_wanted=150,
    hours_old=HOURS_OLD
)
all_jobs.append(jobs2)
total_before_dedup += len(jobs2)
print(f"Found {len(jobs2)} jobs")

# Search 3: Abu Dhabi and Sharjah nursing jobs
print(f"\n[3/7] Searching for nursing jobs in Abu Dhabi and Sharjah (Last 30 days - {HOURS_OLD} hours)...")
jobs3 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="nurse nursing healthcare",
    location="Abu Dhabi",
    results_wanted=150,
    hours_old=HOURS_OLD,
    country_indeed='United Arab Emirates'
)
all_jobs.append(jobs3)
total_before_dedup += len(jobs3)
print(f"Found {len(jobs3)} jobs")

# Search 4: Staff and clinical nurse positions
print(f"\n[4/7] Searching for staff nurse and clinical positions (Last 30 days - {HOURS_OLD} hours)...")
jobs4 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="staff nurse clinical nurse RN",
    location="Dubai",
    results_wanted=150,
    hours_old=HOURS_OLD,
    country_indeed='United Arab Emirates'
)
all_jobs.append(jobs4)
total_before_dedup += len(jobs4)
print(f"Found {len(jobs4)} jobs")

# Search 5: Major hospital groups
print(f"\n[5/7] Searching major hospitals: NMC, Mediclinic, Fakeeh (Last 30 days - {HOURS_OLD} hours)...")
jobs5 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="nurse NMC Mediclinic Fakeeh hospital",
    location="Dubai",
    results_wanted=150,
    hours_old=HOURS_OLD,
    country_indeed='United Arab Emirates'
)
all_jobs.append(jobs5)
total_before_dedup += len(jobs5)
print(f"Found {len(jobs5)} jobs")

# Search 6: Sheikh Shakhbout, Cleveland Clinic, Burjeel hospitals
print(f"\n[6/7] Searching hospitals: Sheikh Shakhbout, Cleveland Clinic, Burjeel (Last 30 days - {HOURS_OLD} hours)...")
jobs6 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="nurse Sheikh Shakhbout Cleveland Clinic Burjeel",
    location="Abu Dhabi",
    results_wanted=150,
    hours_old=HOURS_OLD,
    country_indeed='United Arab Emirates'
)
all_jobs.append(jobs6)
total_before_dedup += len(jobs6)
print(f"Found {len(jobs6)} jobs")

# Search 7: More hospitals
print(f"\n[7/7] Searching hospitals: Saudi German, Aster, Al Zahra (Last 30 days - {HOURS_OLD} hours)...")
jobs7 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="nurse Saudi German Aster Al Zahra hospital",
    location="Dubai",
    results_wanted=150,
    hours_old=HOURS_OLD,
    country_indeed='United Arab Emirates'
)
all_jobs.append(jobs7)
total_before_dedup += len(jobs7)
print(f"Found {len(jobs7)} jobs")

# ============================================================================
# HOSPITAL DIRECT SCRAPING
# ============================================================================

print("\n" + "="*80)
print("Scraping jobs directly from hospital websites...")
print("="*80)

hospital_jobs = []

# Scrape each hospital
try:
    hospital_jobs.extend(scrape_nmc_healthcare())
except Exception as e:
    print(f"NMC scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_kings_college())
except Exception as e:
    print(f"Kings College scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_burjeel_holdings())
except Exception as e:
    print(f"Burjeel scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_mediclinic())
except Exception as e:
    print(f"Mediclinic scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_cleveland_clinic())
except Exception as e:
    print(f"Cleveland Clinic scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_aster_dm())
except Exception as e:
    print(f"Aster scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_saudi_german())
except Exception as e:
    print(f"Saudi German scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_thumbay())
except Exception as e:
    print(f"Thumbay scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_american_hospital_dubai())
except Exception as e:
    print(f"American Hospital scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_al_zahra())
except Exception as e:
    print(f"Al Zahra scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_zulekha())
except Exception as e:
    print(f"Zulekha scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_fakeeh())
except Exception as e:
    print(f"Dr. Sulaiman Al Habib scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_emirates_hospital())
except Exception as e:
    print(f"Emirates Hospital scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_rak_hospital())
except Exception as e:
    print(f"RAK Hospital scraping failed: {e}")

try:
    hospital_jobs.extend(scrape_healthpoint())
except Exception as e:
    print(f"Healthpoint scraping failed: {e}")

print(f"\nTotal hospital jobs found: {len(hospital_jobs)}")

# ============================================================================
# PROCESSING NEW JOBS (JobSpy + Hospital Direct)
# ============================================================================

print("\n" + "="*80)
print("Processing new jobs...")

# Process JobSpy results
jobs = pd.concat(all_jobs, ignore_index=True)
jobs = jobs.drop_duplicates(subset=['job_url'], keep='first')

# Convert date_posted to datetime first
jobs['date_posted'] = pd.to_datetime(jobs['date_posted'], errors='coerce')

# Prepare JobSpy jobs in required format
jobspy_df = pd.DataFrame({
    'Job Title': jobs['title'],
    'Platform': jobs['site'].str.capitalize(),  # Platform column added
    'Company Name': jobs['company'],
    'Description': jobs['description'].str[:500],  # First 500 chars
    'Location': jobs['location'],
    'Work Model': '',  # Empty for now
    'Published': jobs['date_posted'].dt.strftime('%Y-%m-%d'),
    'Salary': jobs.apply(lambda x: f"${x['min_amount']}-${x['max_amount']}"
                         if pd.notna(x.get('min_amount')) and pd.notna(x.get('max_amount'))
                         else '', axis=1),
    'Seniority': '',  # Empty for now
    'Company Size': '',  # Empty for now
    'Industry': 'Healthcare',
    'Apply Link': jobs['job_url'],
    'Source': jobs['site'].str.capitalize() + ' (JobSpy)',
    'Collected At': now_iso(),
    '_uid': ''  # Will be calculated
})

# Add unique ID for JobSpy jobs
jobspy_df['_uid'] = jobspy_df.apply(uid_for, axis=1)

# Convert hospital jobs to DataFrame
if hospital_jobs:
    hospital_df = pd.DataFrame(hospital_jobs)
    # Add unique ID for hospital jobs
    hospital_df['_uid'] = hospital_df.apply(uid_for, axis=1)
else:
    hospital_df = pd.DataFrame()

# Combine JobSpy + Hospital jobs
if not hospital_df.empty:
    new_jobs_df = pd.concat([jobspy_df, hospital_df], ignore_index=True)
    new_jobs_df = new_jobs_df.drop_duplicates(subset=['_uid'], keep='first')
    print(f"JobSpy jobs: {len(jobspy_df)}")
    print(f"Hospital jobs: {len(hospital_df)}")
    print(f"Total after dedup: {len(new_jobs_df)}")
else:
    new_jobs_df = jobspy_df
    print(f"Total jobs scraped: {len(new_jobs_df)} (JobSpy only)")

# ============================================================================
# GOOGLE SHEETS - MERGE WITH EXISTING DATA
# ============================================================================

print("\n" + "="*80)
print("Connecting to Google Sheets...")

try:
    scopes = ['https://spreadsheets.google.com/feeds',
              'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.get_worksheet(0)

    print(f"[OK] Connected to Google Sheet: {sheet.title}")

    # ============================================================================
    # READ EXISTING DATA FROM SHEET
    # ============================================================================
    print("Reading existing data from sheet...")

    existing_data = worksheet.get_all_values()

    if len(existing_data) > 1:  # Has header + data
        existing_df = pd.DataFrame(existing_data[1:], columns=existing_data[0])

        # Make sure _uid column exists in existing data
        if '_uid' not in existing_df.columns:
            existing_df['_uid'] = existing_df.apply(uid_for, axis=1)

        print(f"Existing jobs in sheet: {len(existing_df)}")

        # ============================================================================
        # DELETE OLD JOBS - Keep only current month (last 30 days)
        # ============================================================================
        print("Removing old jobs (keeping only current month - last 30 days)...")

        # Convert Collected At to datetime (timezone-aware)
        existing_df['Collected At'] = pd.to_datetime(existing_df['Collected At'], errors='coerce')

        # Calculate cutoff date (30 days ago) - make it timezone-aware
        from datetime import datetime, timedelta, timezone as tz
        cutoff_date = datetime.now(tz.utc) - timedelta(days=30)

        # Ensure both are timezone-aware for comparison
        if existing_df['Collected At'].dt.tz is None:
            existing_df['Collected At'] = existing_df['Collected At'].dt.tz_localize('UTC')

        # Keep only jobs from last 30 days
        existing_df = existing_df[existing_df['Collected At'] >= cutoff_date]

        # Convert back to string
        existing_df['Collected At'] = existing_df['Collected At'].astype(str)

        print(f"Jobs after cleanup (last 30 days): {len(existing_df)}")

        # ============================================================================
        # MERGE: Keep old + Add only NEW jobs
        # ============================================================================
        print("Merging with new jobs...")

        # Track existing UIDs to detect NEW jobs
        existing_uids = set(existing_df['_uid'].values)
        new_jobs_df['is_new'] = ~new_jobs_df['_uid'].isin(existing_uids)
        new_jobs_count = new_jobs_df['is_new'].sum()

        # Add 🔥 emoji to NEW job titles
        new_jobs_df.loc[new_jobs_df['is_new'], 'Job Title'] = '🔥 ' + new_jobs_df.loc[new_jobs_df['is_new'], 'Job Title'].astype(str)

        # Combine old and new
        combined_df = pd.concat([existing_df, new_jobs_df], ignore_index=True)

        # Remove duplicates (keep first occurrence = old jobs stay)
        combined_df = combined_df.drop_duplicates(subset=['_uid'], keep='first')

        # Sort by Collected At (newest first)
        combined_df['Collected At'] = pd.to_datetime(combined_df['Collected At'], errors='coerce')
        combined_df = combined_df.sort_values(by='Collected At', ascending=False, na_position='last')
        # Convert back to string for Google Sheets
        combined_df['Collected At'] = combined_df['Collected At'].astype(str)

        print(f"🔥 NEW jobs added: {new_jobs_count}")
        print(f"Total jobs now: {len(combined_df)}")

    else:
        # First run - no existing data
        print("No existing data - this is first run")

        # Mark ALL jobs as new with 🔥 emoji
        new_jobs_df['Job Title'] = '🔥 ' + new_jobs_df['Job Title'].astype(str)

        combined_df = new_jobs_df
        combined_df = combined_df.sort_values(by='Collected At', ascending=False)
        print(f"🔥 NEW jobs added: {len(combined_df)}")
        print(f"Total jobs: {len(combined_df)}")

    # ============================================================================
    # ADD DAILY SEPARATORS
    # ============================================================================
    print("\nAdding daily separators...")

    # Convert Collected At back to datetime for grouping
    combined_df['Collected At'] = pd.to_datetime(combined_df['Collected At'], errors='coerce')

    # Sort by date (newest first)
    combined_df = combined_df.sort_values(by='Collected At', ascending=False, na_position='last')

    # Convert back to string
    combined_df['Collected At'] = combined_df['Collected At'].astype(str)

    # ============================================================================
    # UPDATE SHEET WITH MERGED DATA
    # ============================================================================
    print("\nUpdating Google Sheet...")

    # Clear and update
    worksheet.clear()

    # Replace NaN with empty string for Google Sheets
    combined_df = combined_df.fillna('')

    # Convert all datetime/timestamp columns to string
    for col in combined_df.columns:
        if combined_df[col].dtype == 'datetime64[ns]' or 'Timestamp' in str(combined_df[col].dtype):
            combined_df[col] = combined_df[col].astype(str)

    # ============================================================================
    # CREATE SUMMARY TABLE - Count jobs by platform
    # ============================================================================
    print("\nCreating summary table...")

    # Count jobs by Platform
    platform_counts = combined_df['Platform'].value_counts().to_dict()

    # Build summary table
    summary_rows = []
    summary_rows.append(['📊 JOB SOURCES SUMMARY', ''])
    summary_rows.append(['Platform', 'Total Jobs'])

    # Add Indeed count
    indeed_count = platform_counts.get('Indeed', 0)
    summary_rows.append(['Indeed', str(indeed_count)])

    # Add LinkedIn count
    linkedin_count = platform_counts.get('Linkedin', 0)
    summary_rows.append(['LinkedIn', str(linkedin_count)])

    # Add hospital counts
    hospital_total = 0
    for platform, count in sorted(platform_counts.items()):
        if platform not in ['Indeed', 'Linkedin']:
            summary_rows.append([platform, str(count)])
            hospital_total += count

    # Add totals
    summary_rows.append(['', ''])
    summary_rows.append(['TOTAL JobSpy', str(indeed_count + linkedin_count)])
    summary_rows.append(['TOTAL Hospitals', str(hospital_total)])
    summary_rows.append(['GRAND TOTAL', str(len(combined_df))])
    summary_rows.append(['', ''])

    # Prepare data with summary table at top
    data_to_upload = summary_rows + [[''], ['']]  # Add 2 blank rows after summary
    data_to_upload.append(combined_df.columns.values.tolist())  # Then column headers

    current_month = None
    current_date = None
    date_separator_rows = []  # Track rows for date separators (blue)
    month_separator_rows = []  # Track rows for month headers (green)

    for idx, row in combined_df.iterrows():
        # Parse collected_at to get date
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
                month_separator_rows.append(len(data_to_upload))  # Track for green color
                current_date = None  # Reset date tracking for new month

            # Add DAILY separator if date changed
            if current_date != date_key:
                current_date = date_key
                # Show date in readable format with day name
                date_label = f"📅 {collected_date.strftime('%A, %B %d, %Y')}"
                date_row = [date_label] + [''] * (len(combined_df.columns) - 1)
                data_to_upload.append(date_row)
                date_separator_rows.append(len(data_to_upload))  # Track for blue color
        except:
            pass

        # Add actual job data
        data_to_upload.append(row.values.tolist())

    # Upload
    worksheet.update(data_to_upload, 'A1')

    # Calculate summary table size
    summary_table_rows = len(summary_rows) + 2  # +2 for blank rows

    # ========================================================================
    # FORMATTING - Summary Table
    # ========================================================================
    print("Formatting summary table...")

    # Format summary title row (row 1) - Blue background
    worksheet.format('A1:B1', {
        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
        "textFormat": {
            "bold": True,
            "fontSize": 13,
            "fontFamily": "Arial",
            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
        },
        "horizontalAlignment": "CENTER"
    })

    # Format summary header row (row 2) - Light blue
    worksheet.format('A2:B2', {
        "backgroundColor": {"red": 0.7, "green": 0.8, "blue": 1.0},
        "textFormat": {
            "bold": True,
            "fontSize": 11,
            "fontFamily": "Arial"
        },
        "horizontalAlignment": "CENTER"
    })

    # Format summary data rows
    summary_end_row = len(summary_rows)
    worksheet.format(f'A3:B{summary_end_row}', {
        "textFormat": {
            "fontSize": 10,
            "fontFamily": "Arial"
        }
    })

    # Bold the total rows
    totals_start = summary_end_row - 3  # Last 3 rows before blank
    worksheet.format(f'A{totals_start}:B{summary_end_row}', {
        "textFormat": {
            "bold": True,
            "fontSize": 11,
            "fontFamily": "Arial"
        }
    })

    # ========================================================================
    # FORMATTING - Job Data Header
    # ========================================================================
    header_row = summary_table_rows + 1  # Header is after summary + blanks

    # Format header row (blue background, white text, bold, centered)
    worksheet.format(f'A{header_row}:O{header_row}', {
        "backgroundColor": {"red": 0.27, "green": 0.45, "blue": 0.77},
        "textFormat": {
            "bold": True,
            "fontSize": 11,
            "fontFamily": "Arial",
            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
        },
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE"
    })

    # Freeze header row (including summary table)
    worksheet.freeze(rows=header_row)

    # Format all data cells - Wrap text, Arial font
    data_start_row = header_row + 1
    last_row = len(data_to_upload)
    worksheet.format(f'A{data_start_row}:O{last_row}', {
        "wrapStrategy": "WRAP",  # Wrap text in cells
        "textFormat": {
            "fontSize": 10,
            "fontFamily": "Arial"
        },
        "verticalAlignment": "TOP"
    })

    # Set column widths for better readability
    try:
        worksheet.columns_auto_resize(0, len(combined_df.columns) - 1)
    except:
        pass  # If auto-resize fails, continue anyway

    # ========================================================================
    # FORMATTING FOR MONTH AND DATE SEPARATORS
    # ========================================================================
    print("Adding highlights for month and date separators...")

    # Green highlight for month headers
    for row_num in month_separator_rows:
        try:
            worksheet.format(f'A{row_num}:O{row_num}', {
                "backgroundColor": {"red": 0.0, "green": 0.7, "blue": 0.0},  # Dark Green
                "textFormat": {
                    "bold": True,
                    "fontSize": 13,
                    "fontFamily": "Arial",
                    "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}  # White text
                },
                "horizontalAlignment": "CENTER"
            })
        except:
            pass

    # Blue highlight for daily separators
    for row_num in date_separator_rows:
        try:
            worksheet.format(f'A{row_num}:O{row_num}', {
                "backgroundColor": {"red": 0.3, "green": 0.6, "blue": 1.0},  # Light Blue
                "textFormat": {
                    "bold": True,
                    "fontSize": 11,
                    "fontFamily": "Arial",
                    "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}  # White text
                },
                "horizontalAlignment": "CENTER"
            })
        except:
            pass  # Continue if formatting fails

    print("[OK] Google Sheet updated successfully!")
    print(f"[OK] Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("="*80)
    print(f"\nSUCCESS! Sheet now has {len(combined_df)} total jobs!")
    print(f"Latest jobs are on top (sorted by Collected At)")
    print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # ========================================================================
    # FINAL STATUS SUMMARY
    # ========================================================================
    run_status["success"] = True
    run_status["total_jobs_in_sheet"] = len(combined_df)
    run_status["new_jobs_added"] = new_jobs_count if 'new_jobs_count' in locals() else 0

    end_time = datetime.now()
    duration = (end_time - run_status["start_time"]).total_seconds()

    print("\n" + "="*80)
    print("📊 AGENT RUN SUMMARY")
    print("="*80)
    log_status(f"Total runtime: {int(duration)} seconds ({duration/60:.1f} minutes)", "INFO")
    log_status(f"JobSpy searches: 7/7 completed", "SUCCESS")
    log_status(f"Hospital scrapers: 15 attempted", "INFO")
    log_status(f"Jobs scraped this run: {len(new_jobs_df)}", "SUCCESS")
    log_status(f"🔥 NEW jobs added to sheet: {run_status['new_jobs_added']}", "SUCCESS")
    log_status(f"📝 Total jobs in sheet: {run_status['total_jobs_in_sheet']}", "SUCCESS")
    log_status(f"Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}", "INFO")
    log_status(f"Agent finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}", "SUCCESS")
    print("="*80)

    if run_status["errors"]:
        print("\n⚠️ ERRORS ENCOUNTERED:")
        for error in run_status["errors"]:
            print(f"  - {error}")
    else:
        log_status("No errors! Clean run ✓", "SUCCESS")

    print("="*80)

except FileNotFoundError:
    log_status("service_account.json file not found!", "ERROR")
    run_status["errors"].append("Missing service_account.json")
    run_status["success"] = False
    print("\n[ERROR] service_account.json file not found!")
    print("="*80)
except Exception as e:
    log_status(f"Failed to update Google Sheets: {e}", "ERROR")
    run_status["errors"].append(str(e))
    run_status["success"] = False
    print(f"\n[ERROR] Failed to update Google Sheets: {e}")
    print("="*80)

# Print final status
print("\n" + "="*80)
if run_status["success"]:
    log_status("✅ AGENT RUN COMPLETED SUCCESSFULLY!", "SUCCESS")
else:
    log_status("❌ AGENT RUN FAILED - CHECK ERRORS ABOVE", "ERROR")
print("="*80)
