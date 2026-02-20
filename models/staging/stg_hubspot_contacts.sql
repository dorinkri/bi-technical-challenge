-- Contact (person) records from HubSpot CRM.
-- Lives in staging because it's just a clean version of the raw source, without logic.

with source as (
    select * from {{ ref('hubspot_contacts') }}
),

renamed as (
    select
        contact_id,
        first_name,
        last_name,
        email,
        job_title,
        lifecycle_stage,
        hubspot_company_id as company_id,
        safe_cast(create_date as datetime) as created_at
    from source
)

select * from renamed