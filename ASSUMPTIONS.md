# Assumptions Log

## Definitions & Scope

- **"Customer"** is defined as a company with at least one closed-won deal in HubSpot. The contacts `lifecycle_stage` field was considered but not used as the primary source, since it showed a slightly different count (28 vs 26).
- **"ACV"** is treated as simple average deal value across closed-won deals.
- **"Active user"** for retention purposes, active user is any user who generated at least one backend event in a given month.
- **"Cohort month"** is the calendar month of a user's earliest event in the backend_events table.

---

## Data Quality Decisions

- The `backend_events.organization_id` field does not match any `company_id` in `hubspot_companies`. These appear to be different internal identifiers. No attempt was made to join across these fields.
- The contacts table was reviewed but not used as a primary source for any of the three main questions. It was useful for supporting context — for example, getting to know the top job titles (Regulatory Specialist, Compliance Officer, QA/RA Engineer).
- `hubspot_deals` contains a `date_entered_pitching` count (75) that exceeds `date_entered_pre_pitch` (69). This suggests some deals skipped the Pre-pitch stage in HubSpot. This was flagged as a data quality observation rather than corrected, since I don't know if this was intentional.
- All 31 closed-won deals had a non-null amount.
- The current month was excluded from retention analysis as it is incomplete and would understate retention rates.

---

## Tooling Decisions

- dbt was used for all transformations. Seeds were used to load the raw CSVs into BigQuery.
- BigQuery was used as the data warehouse (dbt-fusion adapter).
- Streamlit + Plotly was chosen for the dashboard to keep everything within the same codebase.
- The dashboard reads directly from the CSV seed files rather than querying BigQuery, to keep the submission runnable without warehouse credentials.
- AI was used throughout this challenge to accelerate development - primarily for debugging dbt errors, documentation, and sense-checking analysis logic. In addition, Streamlit was new to me, and I used AI to learn the library as part of the challenge.