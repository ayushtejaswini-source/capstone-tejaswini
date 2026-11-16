# CareClick Clinics: Appointment No-Show Prediction

An end-to-end analytics capstone that cleans synthetic appointment data, analyzes clinic no-show trends, predicts booking risk, and turns follow-up notes into a prioritized call list.

## Project guide

The full project documentation, setup instructions, methodology, SQL analysis, model results, and limitations are in the [project README](careclick-noshow-prediction/README.md).

## Project components

- **Data preparation:** standardizes appointment records and enriches them with clinic weather.
- **SQL analysis:** answers operational questions about clinic, lead time, reminders, and patient history.
- **Machine learning:** compares and tunes models using validation data, then evaluates the selected model on a held-out test set.
- **Follow-up analysis:** structures synthetic call notes and combines them with risk scores to prioritize outreach.

All patient and appointment records in this repository are synthetic. Optional MySQL and Gemini integrations require local credentials; the notebooks include SQLite and rule-based fallbacks.
