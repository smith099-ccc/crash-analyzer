# Crash Analyzer Android

This repository is configured to build an Android APK automatically with GitHub Actions.

## Build
- Push to main, or use Actions -> Build Crash Analyzer APK -> Run workflow.
- When the workflow finishes, open the run and download the artifact named crash-analyzer-debug-apk.
- Extract the artifact ZIP and install the APK on Android.

## Current dashboard
- Latest 40 valid multiplier values
- Actual sample size
- 1.35x–1.47x target statistics
- Below/above target counts
- Median
- Observed target-range percentage
- Model-generated 75%–93% probability/confidence estimate based on historical statistics

The current Android build accepts multiplier values pasted into the app. The existing rendered-page collector is retained separately because the Playwright/Chromium collector is not an Android runtime dependency.
