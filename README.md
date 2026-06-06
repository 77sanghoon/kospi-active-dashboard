# KOSPI Active ETF Dashboard

This repository runs a scheduled GitHub Actions workflow for the KOSPI active ETF dashboard.

The workflow restores the bundled project source, collects holdings for five ETFs, writes daily worksheets to Google Sheets, and deploys the dashboard to GitHub Pages.

## Required GitHub Secrets

Add these in Settings > Secrets and variables > Actions:

- `GOOGLE_SPREADSHEET_ID`: the target Google Sheets spreadsheet ID
- `GOOGLE_SERVICE_ACCOUNT_JSON`: full Google service account JSON

Alternatively, use `GOOGLE_SERVICE_ACCOUNT_B64` instead of `GOOGLE_SERVICE_ACCOUNT_JSON`.

The Google service account email must be shared as an editor on the target spreadsheet.

## First Run

1. Settings > Pages: set Source to GitHub Actions.
2. Actions > KOSPI Active Daily Collector > Run workflow.
3. For a quick connection test, use `latest_only=true`.

The workflow is scheduled for `0 1 * * 1-5` UTC, which is 10:00 KST on weekdays.
