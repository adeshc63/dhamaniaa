# LinkedIn Job Automation - Setup Guide

## Overview
Your JobSpy agent now has **3 separate automation schedules**:

### 1. **Hourly Scraper** (Original)
- **File**: `agent.py`
- **Workflow**: `.github/workflows/scrape.yml`
- **Schedule**: Every hour (`0 * * * *`)
- **Platforms**: Indeed + LinkedIn
- **Search Range**: Last 30 days (720 hours)
- **Purpose**: Comprehensive search across all platforms

### 2. **15-Minute LinkedIn Scraper** (NEW)
- **File**: `agent_linkedin_15min.py`
- **Workflow**: `.github/workflows/scrape_linkedin_15min.yml`
- **Schedule**: Every 15 minutes (`*/15 * * * *`)
- **Platform**: LinkedIn ONLY
- **Search Range**: Last 1 hour
- **Purpose**: Catch fresh LinkedIn jobs immediately
- **Searches**: 3 targeted searches (Dubai, DHA, Abu Dhabi)
- **Results per search**: 50 jobs

### 3. **Daily LinkedIn Scraper** (NEW)
- **File**: `agent_linkedin_24hr.py`
- **Workflow**: `.github/workflows/scrape_linkedin_24hr.yml`
- **Schedule**: Once per day at midnight UTC (`0 0 * * *`)
- **Platform**: LinkedIn ONLY
- **Search Range**: Last 7 days (168 hours)
- **Purpose**: Comprehensive daily LinkedIn sweep
- **Searches**: 5 comprehensive searches (Dubai, DHA, Abu Dhabi, Sharjah, UAE-wide)
- **Results per search**: 150-200 jobs

## How It Works

### Job Deduplication
All three scrapers share the same Google Sheet and use UID-based deduplication:
- Each job gets a unique MD5 hash based on: Title + Company + Location + URL
- Only NEW jobs (not in sheet) are added
- No duplicates even when running multiple scrapers

### Daily Separators
All scrapers add jobs with daily date separators:
- **Green headers**: Month separators (e.g., "═══════════ NOVEMBER 2025 ═══════════")
- **Blue headers**: Daily separators (e.g., "📅 Sunday, November 10, 2025")

### Status Logging
Each scraper provides detailed run statistics:
```
📊 RUN SUMMARY
✅ Total runtime: 45 seconds
✅ LinkedIn searches: 3/3 completed
✅ Jobs scraped this run: 127
🔥 NEW jobs added to sheet: 15
📝 Total jobs in sheet: 1,542
```

## GitHub Actions Setup

### Activate the Workflows

1. **Push to GitHub** (if not already pushed):
```bash
git push origin main
```

2. **Enable GitHub Actions**:
   - Go to: https://github.com/adeshc63/dhamaniaa/actions
   - If workflows are disabled, click "Enable workflows"

3. **Verify Workflows**:
   You should see 3 workflows:
   - "UAE Nursing Jobs Scraper" (hourly)
   - "LinkedIn Jobs - Every 15 Minutes"
   - "LinkedIn Jobs - Daily (24 Hours)"

4. **Manual Test**:
   - Click on each workflow
   - Click "Run workflow" → "Run workflow"
   - Wait 2-3 minutes and check the logs

### Secrets Required
Make sure these secrets are set in your repository:
- `SERVICE_ACCOUNT_JSON` - Google Sheets service account credentials
- `SHEET_ID` - Your Google Sheet ID: `1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU`

## Expected Behavior

### Hourly Scraper (Every Hour at :00)
```
10:00 - Scrapes Indeed + LinkedIn (last 30 days)
11:00 - Scrapes Indeed + LinkedIn (last 30 days)
12:00 - Scrapes Indeed + LinkedIn (last 30 days)
```

### 15-Minute LinkedIn Scraper
```
10:00 - LinkedIn only (last 1 hour)
10:15 - LinkedIn only (last 1 hour)
10:30 - LinkedIn only (last 1 hour)
10:45 - LinkedIn only (last 1 hour)
11:00 - LinkedIn only (last 1 hour)
```

### Daily LinkedIn Scraper (Midnight UTC)
```
00:00 UTC - Comprehensive LinkedIn search (last 7 days)
```

## Benefits of This Setup

1. **Fresh Jobs**: 15-minute scraper catches LinkedIn jobs within 1 hour of posting
2. **No Missed Jobs**: Daily scraper ensures weekend jobs are captured
3. **Comprehensive Coverage**: Hourly scraper covers Indeed + LinkedIn
4. **No Duplicates**: All scrapers share deduplication logic
5. **Cost Efficient**: 15-minute scraper only searches last 1 hour (faster, fewer API calls)

## Monitoring

### Check Run History
- Go to: https://github.com/adeshc63/dhamaniaa/actions
- Click on each workflow to see run history
- Green checkmark ✅ = Success
- Red X ❌ = Failed (check logs)

### View Logs
- Click on any workflow run
- Click on "scrape" job
- Expand steps to see detailed logs with timestamps

## Troubleshooting

### If workflows don't run automatically:
1. Check GitHub Actions is enabled for your repository
2. Verify secrets are set correctly
3. Try manual "Run workflow" button
4. Check workflow file syntax at: `.github/workflows/`

### If getting "No new jobs" constantly:
- 15-minute scraper searches last 1 hour only (may find fewer jobs)
- This is normal - only adds jobs if they're genuinely new
- Daily scraper searches 7 days (will find more)

### If getting rate limits:
- LinkedIn may block if too many requests
- GitHub Actions has usage limits (2,000 minutes/month for free)
- Consider reducing 15-min scraper frequency if needed

## Next Steps

1. **Push these changes to GitHub**
2. **Enable workflows in GitHub Actions**
3. **Run manual test of each workflow**
4. **Monitor Google Sheet for new jobs**
5. **Check logs after first automatic run**

## Files Created

```
.github/workflows/
  ├── scrape.yml                    # Hourly (existing)
  ├── scrape_linkedin_15min.yml     # Every 15 minutes (NEW)
  └── scrape_linkedin_24hr.yml      # Daily (NEW)

agent/
  ├── agent.py                      # Hourly scraper (existing)
  ├── agent_linkedin_15min.py       # 15-minute scraper (NEW)
  └── agent_linkedin_24hr.py        # 24-hour scraper (NEW)
```

---

**Created**: November 10, 2025
**Status**: Ready to deploy ✅
