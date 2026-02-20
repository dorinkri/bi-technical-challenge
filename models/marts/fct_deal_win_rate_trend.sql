-- This model answers: is the win rate improving or declining over time?

-- One row per month for all closed deals, with monthly win rate and a half-year smoothed rate to make the trend easier to read.

with deals as (
    select * from {{ ref('int_deal_funnel_stages') }}
    where is_closed = true
      and close_date is not null  -- only closed deals have a close_date
),

monthly as (
    select
        close_month,
        close_half_year,
        count(*) as total_closed,
        countif(outcome = 'won') as total_won,
        countif(outcome = 'lost') as total_lost,
        round(countif(outcome = 'won') * 100.0 / count(*), 1) as win_rate_pct,
        round(sum(case when outcome = 'won' then amount end), 0) as won_revenue,
        round(avg(case when outcome = 'won' then amount end), 0) as avg_won_deal_size
    from deals
    group by close_month, close_half_year
),

-- Aggregate to half-year for a smoother trend line (monthly can be noisy with small volumes)
half_yearly as (
    select
        close_half_year,
        round(sum(total_won) * 100.0 / nullif(sum(total_closed), 0), 1) as win_rate_pct
    from monthly
    group by close_half_year
)

select
    m.close_month,
    m.close_half_year,
    m.total_closed,
    m.total_won,
    m.total_lost,
    m.win_rate_pct,
    m.won_revenue,
    m.avg_won_deal_size,
    h.win_rate_pct as half_year_win_rate_pct  -- smoothed version for trend charts (kept this even though I used Streamlit with raw data=)
from monthly m
left join half_yearly h on m.close_half_year = h.close_half_year
order by close_month