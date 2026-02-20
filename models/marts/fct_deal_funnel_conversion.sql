-- This model answers: where in the sales funnel are deals dropping off?

-- It shows how many deals entered each pipeline stage, the drop-off rate vs. the prior stage,
-- and for Contract Negotiation specifically (where most losses probably happen), breaks down
-- win/loss counts, avg deal sizes, and avg days spent before closing.

with deals as (
    select * from {{ ref('int_deal_funnel_stages') }}
),

-- Count how many deals entered each stage, regardless of outcome
stage_entries as (
    select 'Pre-pitch' as stage_name, 1 as stage_order, countif(entered_pre_pitch)            as deals_entered from deals union all
    select 'Pitching' as stage_name, 2 as stage_order, countif(entered_pitching)             as deals_entered from deals union all
    select 'Product Testing' as stage_name, 3 as stage_order, countif(entered_product_testing)      as deals_entered from deals union all
    select 'Price Offering' as stage_name, 4 as stage_order, countif(entered_price_offering)       as deals_entered from deals union all
    select 'Contract Negotiation' as stage_name, 5 as stage_order, countif(entered_contract_negotiation) as deals_entered from deals
),

-- For Contract Negotiation
stage_outcomes as (
    select
        last_stage_reached                                                               as stage_name,
        countif(outcome = 'won')                                                         as deals_won,
        countif(outcome = 'lost')                                                        as deals_lost,
        countif(outcome = 'open')                                                        as deals_open,
        round(avg(case when outcome = 'won'  then days_in_contract_negotiation end), 1) as avg_days_neg_won,
        round(avg(case when outcome = 'lost' then days_in_contract_negotiation end), 1) as avg_days_neg_lost,
        round(avg(case when outcome = 'won'  then amount end), 0)                       as avg_deal_size_won,
        round(avg(case when outcome = 'lost' then amount end), 0)                       as avg_deal_size_lost
    from deals
    where last_stage_reached = 'Contract Negotiation'
    group by 1
),

final as (
    select
        e.stage_name,
        e.stage_order,
        e.deals_entered,

        -- % of deals from the previous stage that made it here
        round(
            e.deals_entered * 100.0 /
            nullif(lag(e.deals_entered) over (order by e.stage_order), 0),
        1) as pct_of_prev_stage,

        -- Contract Negotiation breakdown (null for earlier stages)
        o.deals_won,
        o.deals_lost,
        o.deals_open,
        round(o.deals_won * 100.0 / nullif(o.deals_won + o.deals_lost + o.deals_open, 0), 1) as win_rate_pct,
        o.avg_days_neg_won,
        o.avg_days_neg_lost,
        o.avg_deal_size_won,
        o.avg_deal_size_lost

    from stage_entries e
    left join stage_outcomes o on e.stage_name = o.stage_name
)

select * from final
order by stage_order