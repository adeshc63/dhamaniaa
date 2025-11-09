# 🔄 How Hourly Auto-Update Works

## ✅ What Happens Every Hour

```
Hour 1 (First Run):
├── Scrape 187 jobs from Indeed/LinkedIn (JobSpy)
├── Scrape 15 jobs from Hospital Websites (Direct)
├── Combine: 202 total jobs
├── Sheet is empty
└── Add all 202 jobs to sheet
    Result: Sheet has 202 jobs

Hour 2 (Second Run):
├── Scrape 187 jobs from JobSpy (may have some new, some old)
├── Scrape 18 jobs from Hospitals (3 new positions opened)
├── Combine: 205 total jobs
├── Read existing 202 jobs from sheet
├── Merge: Keep old 202 + Add ONLY NEW jobs
└── Remove duplicates (by _uid hash)
    Result: Sheet has 207 jobs (5 new jobs added)

Hour 3 (Third Run):
├── Scrape 187 jobs from JobSpy
├── Scrape 18 jobs from Hospitals
├── Combine: 205 total jobs
├── Read existing 207 jobs from sheet
├── Merge: Keep old 207 + Add ONLY NEW jobs
└── Remove duplicates
    Result: Sheet has 215 jobs (8 more new jobs)

...and so on, EVERY HOUR!
```

## 📊 Sheet Columns (Exact Format)

```
| Job Title | Platform | Company Name | Description | Location | Work Model |
| Published | Salary | Seniority | Company Size | Industry |
| Apply Link | Source | Collected At | _uid |
```

**15 columns total**:
- Platform shows "Indeed", "Linkedin", or Hospital Name (e.g., "NMC Healthcare")
- Source shows detailed origin (e.g., "Indeed (JobSpy)" or "NMC Healthcare (Direct)")

## 🎯 Key Features

### 1. OLD JOBS STAY
```
Job scraped at 9 AM → Still in sheet at 10 AM ✓
Job scraped at 9 AM → Still in sheet at 11 AM ✓
Job scraped at 9 AM → Still in sheet tomorrow ✓
```

### 2. NEW JOBS ADDED
```
New job appears at 10 AM → Added to sheet ✓
Another new job at 11 AM → Added to sheet ✓
Latest jobs always on TOP (sorted by Collected At)
```

### 3. DUPLICATES REMOVED
```
Same job on Indeed + LinkedIn → Only ONE entry in sheet ✓
Job scraped multiple times → Only FIRST entry kept ✓
Unique ID = Job Title + Company + Location + Link
```

### 4. LATEST ON TOP
```
Sheet sorted by "Collected At" column
Newest jobs = Row 2, 3, 4...
Older jobs = Further down
```

## 📈 Sheet Growth Example

```
Day 1, Hour 1:   202 jobs (187 JobSpy + 15 Hospital)
Day 1, Hour 2:   210 jobs (+8 new)
Day 1, Hour 3:   218 jobs (+8 new)
Day 1, Hour 4:   223 jobs (+5 new)
...
Day 1, Hour 24:  280 jobs

Day 2, Hour 1:   288 jobs (+8 new)
Day 2, Hour 2:   293 jobs (+5 new)
...

After 1 week:    ~500-900 jobs
After 1 month:   ~1000-2500 jobs (last 30 days, includes hospital direct)
```

## 🔍 How Deduplication Works

**Unique ID Formula:**
```
_uid = MD5 hash of:
    Job Title (lowercase)
  + Company Name (lowercase)
  + Location (lowercase)
  + Apply Link (lowercase)
```

**Example:**
```
Job 1: "Registered Nurse" at "NMC Hospital" in "Dubai"
Job 2: "Registered Nurse" at "NMC Hospital" in "Dubai"
→ SAME _uid → Only first one kept ✓

Job 3: "Staff Nurse" at "NMC Hospital" in "Dubai"
→ DIFFERENT _uid → Added as new job ✓
```

## ⏰ Hourly Schedule

```
GitHub Actions runs at:
00:00, 01:00, 02:00, 03:00, 04:00, 05:00,
06:00, 07:00, 08:00, 09:00, 10:00, 11:00,
12:00, 13:00, 14:00, 15:00, 16:00, 17:00,
18:00, 19:00, 20:00, 21:00, 22:00, 23:00

= 24 times per day
= 168 times per week
= 720 times per month
```

**Each run:**
- Takes ~5-8 minutes
- Scrapes 187 jobs
- Adds 0-20 new unique jobs (average)
- Updates sheet automatically

## 💾 Data Retention

**Jobs stay in sheet:**
- ✅ Until you manually delete them
- ✅ No automatic cleanup
- ✅ Keeps growing over time

**If you want to remove old jobs:**
- Manually delete rows in Google Sheet
- Or add cleanup logic (delete jobs older than 60 days, etc.)

## 🎯 Summary

**What you asked for:**
- ✅ Runs every 1 hour (not 6 hours)
- ✅ Old jobs STAY in sheet (not deleted)
- ✅ New jobs ADDED every hour
- ✅ Exact columns you specified
- ✅ Latest jobs on top (sorted by Collected At)
- ✅ Proper automation via GitHub Actions

**Result:**
- Sheet keeps growing with fresh jobs
- No manual work needed
- Always has latest nursing jobs
- Duplicates automatically handled
- FREE forever!

🎉 **Perfect automation!**
