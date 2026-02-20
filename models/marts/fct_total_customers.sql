with companies as (
    select * from {{ ref('stg_hubspot_companies') }}
),

deals as (
    select * from {{ ref('stg_hubspot_deals') }}
),

-- Filter for companies that have at least one 'Closed Won' deal
won_deals as (
    select 
        distinct company_id 
    from deals 
    where is_closed_won = True
)

select 
    count(wd.company_id) as total_active_customers
from won_deals wd
join companies c on wd.company_id = c.company_id