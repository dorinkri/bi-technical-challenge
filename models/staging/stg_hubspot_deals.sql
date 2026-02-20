with source as (
    select * from {{ ref('hubspot_deals') }}
),

renamed as (
    select
        deal_id,
        hubspot_company_id as company_id,
        deal_name,
        deal_type,
        currency,
        is_closed,
        is_closed_won,
        cast(amount as numeric) as amount,
        safe_cast(close_date as datetime) as close_date,
        date_entered_closed_won,

        -- Stage entry dates (needed for bonus funnel insight)
        safe_cast(date_entered_pre_pitch as datetime) as entered_pre_pitch_at,
        safe_cast(date_entered_pitching as datetime) as entered_pitching_at,
        safe_cast(date_entered_product_testing as datetime) as entered_product_testing_at,
        safe_cast(date_entered_price_offering as datetime) as entered_price_offering_at,
        safe_cast(date_entered_contract_negotiation as datetime) as entered_contract_negotiation_at,
        safe_cast(date_entered_closed_won as datetime) as entered_closed_won_at,
        safe_cast(date_entered_closed_lost as datetime) as entered_closed_lost_at,
        safe_cast(create_date as datetime) as created_at

    from source
)

select * from renamed