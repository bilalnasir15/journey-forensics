-- ============================================================
-- JOURNEY FORENSICS
-- DAY 3 - ADVANCED SQL
-- CUSTOMER JOURNEY ANALYTICAL SUMMARY
-- PostgreSQL 18
-- ============================================================

-- ============================================================
-- CTE 1: ORDER EVENTS
--
-- Demonstrates:
--   ROW_NUMBER()
--   LAG()
--   LEAD()
--
-- Creates an ordered event stream for every booking.
-- ============================================================

WITH ordered_events AS (

    SELECT

        e.customer_id,
        e.booking_id,
        e.event_id,
        e.event_type,
        e.event_timestamp,

        ROW_NUMBER() OVER (
            PARTITION BY e.booking_id
            ORDER BY e.event_timestamp, e.event_id
        ) AS event_sequence,

        LAG(e.event_type) OVER (
            PARTITION BY e.booking_id
            ORDER BY e.event_timestamp, e.event_id
        ) AS previous_event_type,

        LAG(e.event_timestamp) OVER (
            PARTITION BY e.booking_id
            ORDER BY e.event_timestamp, e.event_id
        ) AS previous_event_timestamp,

        LEAD(e.event_type) OVER (
            PARTITION BY e.booking_id
            ORDER BY e.event_timestamp, e.event_id
        ) AS next_event_type,

        LEAD(e.event_timestamp) OVER (
            PARTITION BY e.booking_id
            ORDER BY e.event_timestamp, e.event_id
        ) AS next_event_timestamp

    FROM events e
),


-- ============================================================
-- CTE 2: EVENT METRICS
--
-- Converts event-level records into booking-level journey
-- metrics.
-- ============================================================

event_metrics AS (

    SELECT

        customer_id,
        booking_id,

        COUNT(*) AS total_events,

        MIN(event_timestamp) AS first_event_timestamp,

        MAX(event_timestamp) AS last_event_timestamp,

        COUNT(*) FILTER (
            WHERE event_type = 'SEARCH'
        ) AS search_events,

        COUNT(*) FILTER (
            WHERE event_type = 'VIEW_TRIP'
        ) AS view_trip_events,

        COUNT(*) FILTER (
            WHERE event_type = 'BOOKING_STARTED'
        ) AS booking_started_events,

        COUNT(*) FILTER (
            WHERE event_type = 'BOOKING_CREATED'
        ) AS booking_created_events,

        COUNT(*) FILTER (
            WHERE event_type = 'PAYMENT_STARTED'
        ) AS payment_started_events,

        COUNT(*) FILTER (
            WHERE event_type = 'PAYMENT_FAILED'
        ) AS payment_failed_events,

        COUNT(*) FILTER (
            WHERE event_type = 'PAYMENT_RETRY'
        ) AS payment_retry_events,

        COUNT(*) FILTER (
            WHERE event_type = 'PAYMENT_COMPLETED'
        ) AS payment_completed_events,

        COUNT(*) FILTER (
            WHERE event_type = 'BOOKING_CONFIRMED'
        ) AS booking_confirmed_events,

        ROUND(
            EXTRACT(
                EPOCH FROM (
                    MAX(event_timestamp)
                    -
                    MIN(event_timestamp)
                )
            ) / 60.0,
            2
        ) AS journey_duration_minutes

    FROM ordered_events

    GROUP BY
        customer_id,
        booking_id
),


-- ============================================================
-- CTE 3: PAYMENT METRICS
--
-- Payment information comes directly from the payments table.
-- We do NOT infer payment transactions from events.
-- ============================================================

payment_metrics AS (

    SELECT

        b.customer_id,
        p.booking_id,

        COUNT(p.payment_id)
            AS payment_attempts,

        COUNT(*) FILTER (
            WHERE p.payment_status = 'Failed'
        ) AS failed_payments,

        COUNT(*) FILTER (
            WHERE p.payment_status = 'Success'
        ) AS successful_payments,

        -- In our generated business logic each failed attempt
        -- represents a retry.
        COUNT(*) FILTER (
            WHERE p.payment_status = 'Failed'
        ) AS retry_count,

        MIN(
            p.payment_timestamp
        ) AS first_payment_timestamp,

        MAX(
            p.payment_timestamp
        ) AS last_payment_timestamp,

        ROUND(
            EXTRACT(
                EPOCH FROM (
                    MAX(p.payment_timestamp)
                    -
                    MIN(p.payment_timestamp)
                )
            ) / 60.0,
            2
        ) AS payment_duration_minutes,

        ROUND(
            (
                COUNT(*) FILTER (
                    WHERE p.payment_status = 'Success'
                )::NUMERIC
                /
                NULLIF(
                    COUNT(p.payment_id),
                    0
                )
            ),
            3
        ) AS payment_success_rate

    FROM payments p

    INNER JOIN bookings b
        ON p.booking_id = b.booking_id

    GROUP BY
        b.customer_id,
        p.booking_id
),


-- ============================================================
-- CTE 4: BOOKING-LEVEL JOURNEY
--
-- Combines:
--   customers
--   bookings
--   trips
--   event metrics
--   payment metrics
--
-- One row = one booking/journey.
-- ============================================================

booking_journey AS (

    SELECT

        c.customer_id,
        c.first_name,
        c.last_name,
        c.country,
        c.customer_segment,

        b.booking_id,
        b.trip_id,
        b.booking_date,
        b.booking_status,
        b.booking_amount,

        t.destination,
        t.trip_type,
        t.departure_date,
        t.return_date,

        -- ----------------------------------------------------
        -- Payment metrics
        -- ----------------------------------------------------

        COALESCE(
            pm.payment_attempts,
            0
        ) AS payment_attempts,

        COALESCE(
            pm.failed_payments,
            0
        ) AS failed_payments,

        COALESCE(
            pm.successful_payments,
            0
        ) AS successful_payments,

        COALESCE(
            pm.retry_count,
            0
        ) AS retry_count,

        COALESCE(
            pm.payment_success_rate,
            0
        ) AS payment_success_rate,

        COALESCE(
            pm.payment_duration_minutes,
            0
        ) AS payment_duration_minutes,

        -- ----------------------------------------------------
        -- Event metrics
        -- ----------------------------------------------------

        COALESCE(
            em.total_events,
            0
        ) AS total_events,

        COALESCE(
            em.search_events,
            0
        ) AS search_events,

        COALESCE(
            em.view_trip_events,
            0
        ) AS view_trip_events,

        COALESCE(
            em.booking_started_events,
            0
        ) AS booking_started_events,

        COALESCE(
            em.booking_created_events,
            0
        ) AS booking_created_events,

        COALESCE(
            em.payment_started_events,
            0
        ) AS payment_started_events,

        COALESCE(
            em.payment_failed_events,
            0
        ) AS payment_failed_events,

        COALESCE(
            em.payment_retry_events,
            0
        ) AS payment_retry_events,

        COALESCE(
            em.payment_completed_events,
            0
        ) AS payment_completed_events,

        COALESCE(
            em.booking_confirmed_events,
            0
        ) AS booking_confirmed_events,

        COALESCE(
            em.journey_duration_minutes,
            0
        ) AS journey_duration_minutes

    FROM customers c

    INNER JOIN bookings b
        ON c.customer_id = b.customer_id

    INNER JOIN trips t
        ON b.trip_id = t.trip_id

    LEFT JOIN payment_metrics pm
        ON b.booking_id = pm.booking_id

    LEFT JOIN event_metrics em
        ON b.booking_id = em.booking_id
),


-- ============================================================
-- CTE 5: CUSTOMER SUMMARY
--
-- Aggregates booking-level journeys to customer level.
-- ============================================================

customer_summary AS (

    SELECT

        customer_id,
        first_name,
        last_name,
        country,
        customer_segment,

        COUNT(DISTINCT booking_id)
            AS total_bookings,

        ROUND(
            SUM(booking_amount),
            2
        ) AS total_booking_value,

        ROUND(
            AVG(booking_amount),
            2
        ) AS average_booking_value,

        -- ----------------------------------------------------
        -- Payment summary
        -- ----------------------------------------------------

        SUM(payment_attempts)
            AS total_payment_attempts,

        SUM(failed_payments)
            AS total_failed_payments,

        SUM(successful_payments)
            AS total_successful_payments,

        SUM(retry_count)
            AS total_retries,

        ROUND(
            (
                SUM(successful_payments)::NUMERIC
                /
                NULLIF(
                    SUM(payment_attempts),
                    0
                )
            ),
            3
        ) AS payment_success_rate,

        -- ----------------------------------------------------
        -- Event summary
        -- ----------------------------------------------------

        SUM(total_events)
            AS total_events,

        SUM(search_events)
            AS search_events,

        SUM(view_trip_events)
            AS view_trip_events,

        SUM(booking_started_events)
            AS booking_started_events,

        SUM(booking_created_events)
            AS booking_created_events,

        SUM(payment_started_events)
            AS payment_started_events,

        SUM(payment_failed_events)
            AS payment_failed_events,

        SUM(payment_retry_events)
            AS payment_retry_events,

        SUM(payment_completed_events)
            AS payment_completed_events,

        SUM(booking_confirmed_events)
            AS booking_confirmed_events,

        -- ----------------------------------------------------
        -- Journey averages
        -- ----------------------------------------------------

        ROUND(
            AVG(journey_duration_minutes),
            2
        ) AS average_journey_duration_minutes,

        ROUND(
            AVG(payment_duration_minutes),
            2
        ) AS average_payment_duration_minutes,

        -- ----------------------------------------------------
        -- Booking outcomes
        -- ----------------------------------------------------

        COUNT(DISTINCT booking_id)
            FILTER (
                WHERE booking_status = 'Confirmed'
            ) AS confirmed_bookings,

        COUNT(DISTINCT booking_id)
            FILTER (
                WHERE booking_status = 'Pending'
            ) AS pending_bookings,

        COUNT(DISTINCT booking_id)
            FILTER (
                WHERE booking_status = 'Cancelled'
            ) AS cancelled_bookings,

        COUNT(DISTINCT booking_id)
            FILTER (
                WHERE failed_payments > 0
            ) AS bookings_with_payment_failures,

        COUNT(DISTINCT booking_id)
            FILTER (
                WHERE retry_count > 0
            ) AS bookings_with_retries,

        COUNT(DISTINCT booking_id)
            FILTER (
                WHERE successful_payments > 0
            ) AS bookings_with_successful_payment

    FROM booking_journey

    GROUP BY

        customer_id,
        first_name,
        last_name,
        country,
        customer_segment
)


-- ============================================================
-- FINAL CUSTOMER-LEVEL RESULT
-- ============================================================

SELECT

    customer_id,
    first_name,
    last_name,
    country,
    customer_segment,

    total_bookings,

    total_booking_value,

    average_booking_value,

    total_payment_attempts,

    total_failed_payments,

    total_successful_payments,

    total_retries,

    payment_success_rate,

    total_events,

    search_events,

    view_trip_events,

    booking_started_events,

    booking_created_events,

    payment_started_events,

    payment_failed_events,

    payment_retry_events,

    payment_completed_events,

    booking_confirmed_events,

    average_journey_duration_minutes,

    average_payment_duration_minutes,

    confirmed_bookings,

    pending_bookings,

    cancelled_bookings,

    bookings_with_payment_failures,

    bookings_with_retries,

    bookings_with_successful_payment

FROM customer_summary

ORDER BY
    total_failed_payments DESC,
    total_retries DESC,
    total_bookings DESC,
    customer_id;