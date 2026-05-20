# CAASPP SBS Chart Tool

This tool helps California parent/community groups make CAASPP charts for a school district.

You do **not** need to install Python. The easiest way is to open the notebook in Google Colab, upload the CAASPP ZIP files you downloaded, and download chart-ready spreadsheets.

## What this makes

The notebook creates files you can upload to Google Sheets:

- a time-series table for CAASPP percent met/exceeded
- an audit table showing exactly which CAASPP rows were used
- a SED/NSED gap table for bar charts
- one Excel workbook with all of the above

## What you need before you start

1. Your district's county code and district code.
   - Example: Las Virgenes Unified = county `19`, district `64683`
   - Example: San Marcos Unified = county `37`, district `73791`
2. CAASPP Smarter Balanced districtwide files from the CAASPP website.
   - Choose **All Student Groups**.
   - ZIP files are okay. Do not unzip them unless you want to.
   - Caret-delimited, comma-delimited, and fixed-width text files are supported.

## Easiest option: run online in Google Colab

After you upload this repo to GitHub, update this link with your GitHub username and repo name:

```text
https://colab.research.google.com/github/isabe11a/caaspp-sbs-chart-tool/blob/main/notebooks/caaspp_sbs_gap_charts.ipynb
```

Then share that Colab link with other chapters.

In Colab, users will:

1. Click **Open in Colab**.
2. Run each step from top to bottom.
3. Upload their CAASPP ZIP files when prompted.
4. Type in their district name, county code, and district code.
5. Download the finished CSV/XLSX files.
6. Upload the XLSX to Google Sheets and make charts.

The uploaded CAASPP files go to the user's temporary Colab session, **not** to your Google Drive.

## Suggested screenshots to add

You may want to add screenshots to your README or notebook showing:

1. Where to click **Open in Colab**.
2. The Colab **play button** next to each step.
3. The file upload box.
4. The district settings cell.
5. The downloaded output files.
6. Uploading the XLSX to Google Sheets.

## Chart labels

For proficiency charts:

- X-axis: `Academic Year`
- Y-axis: `Percent Met or Exceeded Standard`

For SED/NSED gap charts:

- X-axis: `Grade Level` or `Academic Year`
- Y-axis: `NSED–SED Gap, percentage points`

## Important caveat

These are grade-level snapshots, not the same students followed over time. Small districts and small SED subgroups can be noisy, so look for patterns that repeat across multiple grades, subjects, or years.

## For advanced users

Advanced users can also run this locally:

```bash
pip install -r requirements.txt
jupyter notebook
```

Most users should use Google Colab instead.
