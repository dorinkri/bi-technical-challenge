-- This model takes the raw deal data and enriches each deal with useful derived fields:
-- what stage it reached, whether it was won/lost/open, and how long it spent in negotiation.

with deals as (
    select * from {{ ref('stg_hubspot_deals') }}
),

enriched as (
    select
        deal_id,
        deal_name,
        deal_type,
        company_id,
        amount,
        created_at,
        close_date,
        is_closed,
        is_closed_won,

        -- Simple outcome label so downstream models don't need to repeat this logic
        case
            when is_closed_won                   then 'won'
            when is_closed and not is_closed_won then 'lost'
            else                                      'open'
        end as outcome,

        -- The furthest stage this deal reached before closing (or where it's currently stuck)
        case
            when entered_contract_negotiation_at is not null then 'Contract Negotiation'
            when entered_price_offering_at       is not null then 'Price Offering'
            when entered_product_testing_at      is not null then 'Product Testing'
            when entered_pitching_at             is not null then 'Pitching'
            when entered_pre_pitch_at            is not null then 'Pre-pitch'
            else                                                  'Unknown'
        end as last_stage_reached,

        -- Boolean flags: did this deal pass through each stage?
        -- Useful for counting how many deals entered each stage in the funnel model.
        entered_pre_pitch_at            is not null as entered_pre_pitch,
        entered_pitching_at             is not null as entered_pitching,
        entered_product_testing_at      is not null as entered_product_testing,
        entered_price_offering_at       is not null as entered_price_offering,
        entered_contract_negotiation_at is not null as entered_contract_negotiation,

        -- How many days did this deal spend in contract negotiation before closing?
        -- Only populated for deals that both entered negotiation and have a close date.
        case
            when entered_contract_negotiation_at is not null and close_date is not null
            then datetime_diff(close_date, entered_contract_negotiation_at, DAY)
        end as days_in_contract_negotiation,

        -- Total days from deal creation to close
        case
            when close_date is not null and created_at is not null
            then datetime_diff(close_date, created_at, DAY)
        end as days_to_close,

        -- Half-year bucket (e.g. "2025-H1") for smoothed trend analysis
        case
            when close_date is not null then
                concat(
                    cast(extract(year from close_date) as string),
                    '-H',
                    case when extract(month from close_date) <= 6 then '1' else '2' end
                )
        end as close_half_year,

        -- Month bucket for monthly trend analysis
        date_trunc(close_date, MONTH) as close_month

    from deals
)

select * from enriched