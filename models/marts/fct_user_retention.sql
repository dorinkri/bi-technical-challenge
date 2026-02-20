-- Grouping users by the first month they showed up in the backend,
-- then checking what % of them came back in the following months (M1, M2, M3)

with events as (
    select * from {{ ref('stg_backend_events') }}
    where event_at is not null
),

user_first_event as (
    -- Find the month each user first appeared
    -- Everyone who first showed up in the same month belongs to the same cohort
    select
        user_id,
        datetime_trunc(min(event_at), MONTH) as cohort_month
    from events
    group by user_id
),

user_activity_months as (
    -- Find every month each user was active in
    -- A user counts as active in a month if they fired at least one event
    select distinct
        user_id,
        datetime_trunc(event_at, MONTH) as activity_month
    from events
),

retention_table as (
    -- For each user, compare every month they were active against their cohort month
    -- month_number = 0 means they were active in their starting month (expected)
    -- month_number = 1 means they came back the following month, and so on
    select
        u.cohort_month,
        a.activity_month,
        datetime_diff(a.activity_month, u.cohort_month, MONTH) as month_number,
        u.user_id as unique_user_id
    from user_first_event u
    join user_activity_months a on u.user_id = a.user_id
)

select
    cohort_month,

    -- How many users started in this cohort
    count(distinct case when month_number = 0 then unique_user_id end) as starting_users,

    -- How many came back in each subsequent month
    count(distinct case when month_number = 1 then unique_user_id end) as m1_returning,
    count(distinct case when month_number = 2 then unique_user_id end) as m2_returning,
    count(distinct case when month_number = 3 then unique_user_id end) as m3_returning,

    -- Retention rate = returning users / starting users, as a %
    -- nullif avoids a division by zero if a cohort somehow has no starting users
    round(
        count(distinct case when month_number = 1 then unique_user_id end) * 100.0 /
        nullif(count(distinct case when month_number = 0 then unique_user_id end), 0), 2
    ) as retention_rate_m1,
    round(
        count(distinct case when month_number = 2 then unique_user_id end) * 100.0 /
        nullif(count(distinct case when month_number = 0 then unique_user_id end), 0), 2
    ) as retention_rate_m2,
    round(
        count(distinct case when month_number = 3 then unique_user_id end) * 100.0 /
        nullif(count(distinct case when month_number = 0 then unique_user_id end), 0), 2
    ) as retention_rate_m3

from retention_table
-- Drop the current month since it's incomplete and would make retention look worse than it is
where cohort_month < datetime_trunc(current_datetime(), MONTH)
group by cohort_month
order by cohort_month