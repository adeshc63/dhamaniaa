# 🏥 UAE Nursing Jobs Agent - GitHub Automation

Automated job scraper that runs on GitHub Actions every 1 hour.
Scrapes Indeed + LinkedIn + Hospital Websites for nursing jobs in UAE and pushes to Google Sheets.

## 🚀 Features

- ✅ **7 Comprehensive JobSpy Searches**:
  1. General nursing jobs in Dubai
  2. DHA licensed nurses (worldwide)
  3. Abu Dhabi and Sharjah nursing jobs
  4. Staff and clinical nurse positions
  5. Major hospitals (NMC, Mediclinic, Fakeeh)
  6. Premium hospitals (Cleveland, Burjeel)
  7. More hospitals (Saudi German, Aster, Al Zahra)

- ✅ **6 Direct Hospital Scrapers**:
  1. NMC Healthcare (Greenhouse API)
  2. Kings College Hospital Dubai (Greenhouse API)
  3. Burjeel Holdings (Direct Website)
  4. Mediclinic Middle East (Workday API)
  5. Cleveland Clinic Abu Dhabi (Workday API)
  6. Aster DM Healthcare (Direct Website)

- ✅ **Job Platforms**: Indeed, LinkedIn + Hospital Direct
- ✅ **Time Filter**: Last 30 days only (720 hours)
- ✅ **Results**: 150 per search = 1000+ total results
- ✅ **Deduplication**: Automatic duplicate removal across all sources
- ✅ **Sorting**: Newest jobs first (by "Collected At")
- ✅ **Auto-update**: Runs every 1 hour via GitHub Actions
- ✅ **Google Sheets**: Automatic push to your sheet
- ✅ **Merge Logic**: OLD jobs STAY, NEW jobs ADDED hourly

## 📋 Setup Instructions

### 1. Create GitHub Repository

```bash
# Create new repo on GitHub
# Name: nursing-jobs-agent (or any name)
```

### 2. Upload Files

Upload these files to your GitHub repo:
```
nursing-jobs-agent/
├── agent.py
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── scrape.yml
```

### 3. Set Up Google Cloud Service Account

**A. Create Service Account:**
1. Go to: https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Google Sheets API
4. Create Service Account
5. Generate JSON key
6. Download the JSON file

**B. Share Google Sheet:**
1. Open the JSON file
2. Copy the `client_email` value
3. Open your Google Sheet
4. Click "Share"
5. Paste the email
6. Give "Editor" permission

### 4. Set GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions

**Add these secrets:**

1. **SERVICE_ACCOUNT_JSON**
   - Open your downloaded JSON file
   - Copy the ENTIRE content
   - Paste as secret value

2. **SHEET_ID**
   - From your Google Sheet URL:
   - `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
   - Copy `YOUR_SHEET_ID` part
   - Paste as secret value

### 5. Run the Automation

**Option A: Wait for Schedule**
- Runs automatically every 6 hours

**Option B: Manual Trigger**
1. Go to repo → Actions tab
2. Click "UAE Nursing Jobs Scraper"
3. Click "Run workflow"
4. Click green "Run workflow" button

## 📊 Output Format

**Google Sheet Columns:**
- Job Title
- Platform (Indeed/Linkedin/Hospital Name)
- Company Name
- Description (first 500 chars)
- Location
- Work Model
- Published (date)
- Salary (if available)
- Seniority
- Company Size
- Industry (Healthcare)
- Apply Link (direct URL)
- Source (e.g., "Indeed (JobSpy)" or "NMC Healthcare (Direct)")
- Collected At (timestamp)
- _uid (unique identifier for deduplication)

## ⚙️ Configuration

### Change Schedule

Edit `.github/workflows/scrape.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours

# Common schedules:
# - cron: '0 */3 * * *'   # Every 3 hours
# - cron: '0 * * * *'     # Every hour
# - cron: '0 9 * * *'     # Daily at 9 AM UTC
# - cron: '0 0,12 * * *'  # Twice daily (midnight & noon)
```

### Change Search Terms

Edit `agent.py` - modify the search configurations:

```python
# Example: Add more searches
jobs8 = scrape_jobs(
    site_name=ALL_PLATFORMS,
    search_term="ICU nurse critical care",
    location="Dubai",
    results_wanted=150,
    hours_old=HOURS_IN_1_MONTH,
    country_indeed='United Arab Emirates'
)
```

## 🔍 Monitoring

### Check Logs

1. Go to repo → Actions tab
2. Click on latest workflow run
3. Click "scrape" job
4. View logs to see:
   - How many jobs found per search
   - Which platforms worked
   - Any errors
   - Google Sheets update status

### Expected Output

```
[1/7] Dubai nursing: Found 96 jobs
[2/7] DHA worldwide: Found 0 jobs
[3/7] Abu Dhabi: Found 88 jobs
[4/7] Staff nurses: Found 18 jobs
...
[Hospital 1/6] NMC Healthcare: Found 5 jobs
[Hospital 2/6] Kings College: Found 3 jobs
[Hospital 3/6] Burjeel: Found 0 jobs
[Hospital 4/6] Mediclinic: Found 12 jobs
[Hospital 5/6] Cleveland Clinic: Found 8 jobs
[Hospital 6/6] Aster: Found 0 jobs

JobSpy jobs: 187
Hospital jobs: 28
Total after dedup: 210

New unique jobs added: 15
Total jobs now: 225
Pushed to Google Sheets ✓
```

## ❓ Troubleshooting

### Error: "service_account.json not found"
- Check GitHub Secrets are set correctly
- Make sure SERVICE_ACCOUNT_JSON contains valid JSON

### Error: "Permission denied on Google Sheets"
- Make sure service account email has Editor access
- Re-share the sheet if needed

### No jobs found
- Indeed and LinkedIn should always work
- Hospital scrapers may return 0 if no openings
- Check if UAE is correctly specified

### Workflow not running
- Check Actions tab is enabled in repo settings
- Verify cron schedule is correct
- Try manual trigger first

## 📈 Statistics

**Typical Results per Run:**
- Indeed: ~140 jobs
- LinkedIn: ~40 jobs
- Hospital Direct: ~10-30 jobs (varies by openings)
- **Total**: 180-210 unique jobs per run

**After 1 Week (168 hourly runs):**
- ~500-800 total jobs in sheet
- Latest jobs always on top
- Duplicates automatically removed

## 🎯 Cost

- ✅ **GitHub Actions**: FREE (2000 minutes/month)
- ✅ **Google Sheets**: FREE
- ✅ **Google Cloud**: FREE tier sufficient
- ✅ **Total Cost**: $0

## 📝 License

Free to use and modify!

## 🆘 Support

If you encounter issues:
1. Check Actions logs
2. Verify all secrets are set
3. Test service account permissions
4. Check Google Sheet share settings

---

**Made with ❤️ for UAE Nursing Job Seekers**
