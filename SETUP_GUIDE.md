# 🚀 Complete Setup Guide - UAE Nursing Jobs Agent

## ✅ Your Configuration

```
Google Sheet ID: 1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU
Google Sheet URL: https://docs.google.com/spreadsheets/d/1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU/edit
Service Account Email: adesh-12@ultra-surfer-437605-i5.iam.gserviceaccount.com
```

---

## 📋 Step-by-Step Setup

### STEP 1: Share Google Sheet (2 minutes)

1. **Open your Google Sheet**:
   ```
   https://docs.google.com/spreadsheets/d/1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU/edit
   ```

2. **Click "Share" button** (top-right corner)

3. **Add this email**:
   ```
   adesh-12@ultra-surfer-437605-i5.iam.gserviceaccount.com
   ```

4. **Select "Editor" permission**

5. **Uncheck** "Notify people" (no need to send email)

6. **Click "Share"**

✅ Done! Service account now has access.

---

### STEP 2: Create GitHub Repository (3 minutes)

1. **Go to GitHub**: https://github.com/new

2. **Repository settings**:
   ```
   Repository name: nursing-jobs-agent
   Description: Automated UAE nursing jobs scraper
   Public ✓ (or Private if you prefer)
   ```

3. **Click "Create repository"**

✅ Repository created!

---

### STEP 3: Upload Files to GitHub (5 minutes)

**Option A: Via GitHub Website (Easy)**

1. Click "uploading an existing file"

2. **Drag and drop** these files from `E:\aitomation\JobSpy\agent\`:
   - `agent.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`

3. Create folder `.github/workflows/`:
   - Click "Add file" → "Create new file"
   - Type: `.github/workflows/scrape.yml`
   - Paste content from your `scrape.yml` file
   - Commit

**Option B: Via Git Commands**

```bash
cd E:\aitomation\JobSpy\agent

git init
git add .
git commit -m "Initial commit - Nursing jobs automation"
git remote add origin https://github.com/YOUR_USERNAME/nursing-jobs-agent.git
git branch -M main
git push -u origin main
```

✅ Files uploaded!

---

### STEP 4: Get Service Account JSON (You already have it!)

Your service account JSON is at:
```
C:\Users\adesh\service_account.json
```

This file contains the credentials for:
```
adesh-12@ultra-surfer-437605-i5.iam.gserviceaccount.com
```

**Open the file** and copy ALL content (from `{` to `}`)

✅ JSON content copied!

---

### STEP 5: Set GitHub Secrets (3 minutes)

1. **Go to your repository**:
   ```
   https://github.com/YOUR_USERNAME/nursing-jobs-agent
   ```

2. **Click**: Settings → Secrets and variables → Actions

3. **Add Secret #1**:
   - Click "New repository secret"
   - Name: `SERVICE_ACCOUNT_JSON`
   - Value: Paste the ENTIRE content from `service_account.json`
   - Click "Add secret"

4. **Add Secret #2**:
   - Click "New repository secret"
   - Name: `SHEET_ID`
   - Value: `1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU`
   - Click "Add secret"

✅ Secrets configured!

---

### STEP 6: Run the Automation! (1 minute)

**Manual Run (Test First):**

1. Go to **Actions** tab in your repo

2. Click "**UAE Nursing Jobs Scraper**" (left sidebar)

3. Click "**Run workflow**" (right side)

4. Click green "**Run workflow**" button

5. **Wait 5-10 minutes**

6. **Check logs**:
   - Click on the running workflow
   - Click "scrape" job
   - Watch real-time logs

7. **Check Google Sheet**:
   ```
   https://docs.google.com/spreadsheets/d/1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU/edit
   ```

✅ If you see jobs → SUCCESS! 🎉

---

## 📊 What to Expect

### Workflow Logs:
```
[1/7] Dubai nursing: Found 96 jobs
[2/7] DHA worldwide: Found 0 jobs
[3/7] Abu Dhabi: Found 88 jobs
[4/7] Staff nurses: Found 18 jobs
[5/7] NMC/Mediclinic: Found 0 jobs
[6/7] Cleveland/Burjeel: Found 0 jobs
[7/7] Saudi German/Aster: Found 0 jobs

Total jobs: 202
Duplicates removed: 15
UNIQUE JOBS: 187

Jobs by Platform:
  Indeed: 141
  Linkedin: 46

✓ Google Sheet updated!
```

### Google Sheet:
- Header row (blue background)
- 187 jobs sorted by date
- Columns: Portal, Job Title, Employer, Location, etc.

---

## ⏰ Automatic Schedule

After successful manual run, it will run automatically:

**Schedule**: Every 6 hours
```
00:00 UTC (5:30 AM IST)
06:00 UTC (11:30 AM IST)
12:00 UTC (5:30 PM IST)
18:00 UTC (11:30 PM IST)
```

Each run adds NEW jobs and removes OLD ones.

---

## 🔧 Troubleshooting

### ❌ Error: "Permission denied on Google Sheets"

**Solution**:
1. Open sheet: https://docs.google.com/spreadsheets/d/1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU/edit
2. Click "Share"
3. Make sure `adesh-12@ultra-surfer-437605-i5.iam.gserviceaccount.com` has **Editor** access
4. Re-run workflow

### ❌ Error: "service_account.json not found"

**Solution**:
1. Check GitHub Secrets
2. Make sure `SERVICE_ACCOUNT_JSON` contains valid JSON (starts with `{` ends with `}`)
3. Re-paste the entire content from `C:\Users\adesh\service_account.json`

### ❌ Error: "Invalid Sheet ID"

**Solution**:
1. Check GitHub Secret `SHEET_ID`
2. Should be: `1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU`
3. No extra spaces or quotes

### ⚠️ Warning: "Naukri API 406 - recaptcha required"

**This is NORMAL!**
- Naukri Gulf sometimes blocks with recaptcha
- Indeed and LinkedIn will still work
- You'll still get 180+ jobs

### ⚠️ Some searches return 0 jobs

**This is NORMAL!**
- Hospital-specific searches (NMC, Cleveland, etc.) often return 0
- General searches (Dubai, Abu Dhabi) always work
- Total is still 180-200 jobs

---

## 📈 Expected Results

**Typical Run:**
```
Indeed:     ~140 jobs
LinkedIn:   ~40 jobs
Naukri:     ~10 jobs (when not blocked)
────────────────────────
Total:      ~190 unique jobs
```

**Job Types:**
- Registered Nurse (RN)
- Staff Nurse
- Clinical Nurse
- ICU Nurse
- Emergency Nurse
- Pediatric Nurse
- Operating Room Nurse
- Home Care Nurse

**Locations:**
- Dubai
- Abu Dhabi
- Sharjah
- Ajman
- RAK

---

## 🎯 Summary Checklist

- [x] Google Sheet shared with service account
- [x] GitHub repository created
- [x] Files uploaded
- [x] GitHub Secrets configured:
  - [x] `SERVICE_ACCOUNT_JSON`
  - [x] `SHEET_ID`
- [x] Manual workflow run tested
- [x] Jobs appearing in Google Sheet

---

## 🆘 Need Help?

**Check these in order:**

1. **Actions logs** → See what went wrong
2. **Sheet permissions** → Service account has Editor access?
3. **GitHub Secrets** → Both secrets set correctly?
4. **Service account JSON** → Valid JSON format?

---

## 🎉 Success!

If you see jobs in your Google Sheet, you're done!

The automation will now:
- ✅ Run every 6 hours
- ✅ Scrape 7 different searches
- ✅ Remove duplicates
- ✅ Sort by date (newest first)
- ✅ Update Google Sheet automatically
- ✅ FREE forever (GitHub + Google free tiers)

**Happy Job Hunting! 🏥💼**

---

## 📞 Quick Reference

```
Your Google Sheet:
https://docs.google.com/spreadsheets/d/1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU/edit

Service Account:
adesh-12@ultra-surfer-437605-i5.iam.gserviceaccount.com

Sheet ID (for GitHub Secret):
1ZLniqVQ31t8uahAoIflZm6Jy8wM5gMRYOYG-oIhS6KU

Service Account JSON Location:
C:\Users\adesh\service_account.json
```

Everything is ready! Just follow the 6 steps above! 🚀
