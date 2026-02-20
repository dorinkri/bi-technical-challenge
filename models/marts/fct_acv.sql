with deals as (
    select * from {{ ref('stg_hubspot_deals')}}
),

won_deals as (
    select
        amount
    from deals
    where is_closed_won = True
)

select
    sum(amount) as total_revenue,
    count(*) as total_contracts,

    -- Calculating the avg
    round(sum(amount) / count(*), 2) as average_contract_value
from won_deals