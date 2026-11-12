# SportyJet Analyzer

A standalone Android/Kivy app for recording SportyJet multipliers, viewing the most recently imported results, calculating descriptive statistics, and running historical resampling simulations.

## Current MVP
- Local history of up to 5,000 imported results.
- Latest 50 imported results with capture timestamps.
- Mean, median, minimum, maximum, and observed frequency below/above 2.00x.
- 1,000-trial resampling simulator based on the stored sample.
- Link to the official SportyJet game page.

## Important feed limitation
The official SportyJet page explains the crash-game mechanics, but a publicly accessible, verifiable results-history feed has not yet been confirmed. This MVP therefore labels imported results as manual and does not fabricate live values. Automatic updates can be added after a public rendered results source is verified and tested on Android.

## Build
Run from this directory:
`buildozer android debug`

## Responsible interpretation
SportyJet is a crash game. Historical statistics and resampling are descriptive tools, not reliable forecasts of the next independent game outcome and not guarantees of profit.
