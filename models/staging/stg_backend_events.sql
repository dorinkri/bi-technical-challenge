with source as (
    select * from {{ ref('backend_events') }}
),

renamed as (
    select
        event_id,
        event_name,
        safe_cast(event_timestamp as datetime) as event_at,
        user_id,
        organization_id
    from source
)

select * from renamed