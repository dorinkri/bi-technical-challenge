with source as (
    select * from {{ ref('hubspot_companies') }}
),

renamed as (
    select
        company_id,
        company_name,
        domain,
        industry,
        country,
        number_of_employees,
        create_date as created_at
    from source
)

select * from renamed