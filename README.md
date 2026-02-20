# Flinn BI Challenge - README

## Q1 - How many customers do we have today?

**Answer: 26 customers**

A customer is defined as any company with at least one closed-won deal in HubSpot. I counted distinct company IDs from closed-won deals and joined them to the companies table to confirm they exist as records.

**Assumptions**
- The deals table is the source of truth for customer status, not the `lifecycle_stage` field in contacts.
- A company counts as a customer regardless of how many deals won.

**Data Quality Notes**
- The contacts table shows 28 companies with a `customer` lifecycle stage, vs. 26 from deal data. The two sources don't fully align - worth checking which should be treated as the source of truth.

---

## Q2 - What is our Average Contract Value (ACV)?

**Answer: €12,967.74 ACV - based on €402,000 total revenue across 31 closed-won deals**

I filtered deals to closed-won only, then calculated the average of deal amounts. All 31 won deals had a non-null amount, so no imputation was needed.

**Assumptions**
- ACV is treated here as average deal value, not annualised contract value.
- All amounts are in EUR as indicated by the currency field.

---

## Q3 - What is the retention of our users?

**Answer: High retention across all cohorts - M1 is consistently 100%, with M2 and M3 occasionally dipping slightly lower for some cohorts**

I grouped users by their first event month (cohort), then checked what percentage returned in each subsequent month (M1, M2, M3). Retention is calculated as returning users divided by cohort starting users.

**Assumptions**
- A user is considered retained in a given month if they generated at least one backend event that month.
- Cohort month is determined by the earliest event timestamp per user.
- The current incomplete month is excluded from the analysis.

---

## Bonus - The Contract Negotiation Bottleneck

Looking at the pipeline data, a pattern emerges: most deals that are lost have already passed through the early stages successfully. The drop-off is concentrated at Contract Negotiation - the final stage before closing.

- 37 deals were lost in total.
- 30 of those (81%) had Contract Negotiation as their last stage before being marked lost
- Of the 55 deals that entered Contract Negotiation: 20 won (36%), 30 lost (55%), 5 still open (9%)
- Average deal size for won vs lost deals in negotiation is similar (€12,875 vs €11,767) — suggesting price is not the deciding factor

---

## Tools Used
- **dbt** (dbt-fusion) for all data transformations
- **BigQuery** as the data warehouse
- **Streamlit + Plotly + pandas + matplotlib** for the dashboard
- **AI** was used primarily for debugging dbt errors, documentation, and sense-checking analysis logic. In addition, Streamlit was new to me, and I used AI to learn the library as part of the challenge.
