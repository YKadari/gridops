with hours as (

    select generate_series(
        '2024-01-01 00:00:00+00'::timestamptz,
        '2025-12-31 23:00:00+00'::timestamptz,
        interval '1 hour'
    ) as target_at

),

calendar as (

    select
        target_at,

        (
            target_at
            at time zone 'America/New_York'
        )::date as local_date

    from hours

),

holiday_dates as (

    select
        holiday_date::date as holiday_date,
        holiday_name

    from {{ ref('us_federal_holidays') }}

)

select
    calendar.target_at,
    calendar.local_date,

    holiday.holiday_date is not null
        as is_holiday,

    next_holiday.holiday_date is not null
        as is_day_before_holiday,

    previous_holiday.holiday_date is not null
        as is_day_after_holiday

from calendar

left join holiday_dates as holiday
    on calendar.local_date
        = holiday.holiday_date

left join holiday_dates as next_holiday
    on calendar.local_date + 1
        = next_holiday.holiday_date

left join holiday_dates as previous_holiday
    on calendar.local_date - 1
        = previous_holiday.holiday_date