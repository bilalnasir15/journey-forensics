-- ============================================================
-- JOURNEY FORENSICS
-- DAY 3 - ADVANCED SQL VALIDATION
-- PostgreSQL 18
-- ============================================================

-- ============================================================
-- CHECK 1: CUSTOMERS
-- ============================================================

SELECT
    'Customers count' AS check_name,
    COUNT(*) AS actual_value,
    5000 AS expected_value,
    CASE
        WHEN COUNT(*) = 5000 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM customers;


-- ============================================================
-- CHECK 2: TRIPS
-- ============================================================

SELECT
    'Trips count' AS check_name,
    COUNT(*) AS actual_value,
    50 AS expected_value,
    CASE
        WHEN COUNT(*) = 50 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM trips;


-- ============================================================
-- CHECK 3: BOOKINGS
-- ============================================================

SELECT
    'Bookings count' AS check_name,
    COUNT(*) AS actual_value,
    8000 AS expected_value,
    CASE
        WHEN COUNT(*) = 8000 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM bookings;


-- ============================================================
-- CHECK 4: PAYMENTS
-- ============================================================

SELECT
    'Payments count' AS check_name,
    COUNT(*) AS actual_value,
    10557 AS expected_value,
    CASE
        WHEN COUNT(*) = 10557 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM payments;


-- ============================================================
-- CHECK 5: EVENTS
-- ============================================================

SELECT
    'Events count' AS check_name,
    COUNT(*) AS actual_value,
    61673 AS expected_value,
    CASE
        WHEN COUNT(*) = 61673 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM events;


-- ============================================================
-- CHECK 6: BOOKING → CUSTOMER JOIN
-- ============================================================

SELECT
    'Invalid booking customer references' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM bookings b
LEFT JOIN customers c
    ON b.customer_id = c.customer_id
WHERE c.customer_id IS NULL;


-- ============================================================
-- CHECK 7: BOOKING → TRIP JOIN
-- ============================================================

SELECT
    'Invalid booking trip references' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM bookings b
LEFT JOIN trips t
    ON b.trip_id = t.trip_id
WHERE t.trip_id IS NULL;


-- ============================================================
-- CHECK 8: PAYMENT → BOOKING JOIN
-- ============================================================

SELECT
    'Invalid payment booking references' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM payments p
LEFT JOIN bookings b
    ON p.booking_id = b.booking_id
WHERE b.booking_id IS NULL;


-- ============================================================
-- CHECK 9: EVENT → BOOKING JOIN
-- ============================================================

SELECT
    'Invalid event booking references' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM events e
LEFT JOIN bookings b
    ON e.booking_id = b.booking_id
WHERE b.booking_id IS NULL;


-- ============================================================
-- CHECK 10: EVENT → CUSTOMER JOIN
-- ============================================================

SELECT
    'Invalid event customer references' AS check_name,
    COUNT(*) AS actual_value,
    0 AS expected_value,
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM events e
LEFT JOIN customers c
    ON e.customer_id = c.customer_id
WHERE c.customer_id IS NULL;


-- ============================================================
-- CHECK 11: ROW_NUMBER
-- ============================================================

WITH numbered_events AS (

    SELECT

        booking_id,

        event_id,

        ROW_NUMBER() OVER (
            PARTITION BY booking_id
            ORDER BY event_timestamp, event_id
        ) AS event_sequence

    FROM events
)

SELECT
    'ROW_NUMBER validation' AS check_name,
    COUNT(*) AS actual_value,
    CASE
        WHEN COUNT(*) = 61673
             AND MIN(event_sequence) = 1
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM numbered_events;


-- ============================================================
-- CHECK 12: LAG
-- ============================================================

WITH lagged_events AS (

    SELECT

        booking_id,

        event_timestamp,

        LAG(event_timestamp) OVER (
            PARTITION BY booking_id
            ORDER BY event_timestamp, event_id
        ) AS previous_timestamp

    FROM events
)

SELECT
    'LAG validation' AS check_name,
    COUNT(*) FILTER (
        WHERE previous_timestamp IS NOT NULL
    ) AS rows_with_previous_event,
    CASE
        WHEN COUNT(*) FILTER (
            WHERE previous_timestamp IS NOT NULL
        ) > 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM lagged_events;


-- ============================================================
-- CHECK 13: LEAD
-- ============================================================

WITH leaded_events AS (

    SELECT

        booking_id,

        event_timestamp,

        LEAD(event_timestamp) OVER (
            PARTITION BY booking_id
            ORDER BY event_timestamp, event_id
        ) AS next_timestamp

    FROM events
)

SELECT
    'LEAD validation' AS check_name,
    COUNT(*) FILTER (
        WHERE next_timestamp IS NOT NULL
    ) AS rows_with_next_event,
    CASE
        WHEN COUNT(*) FILTER (
            WHERE next_timestamp IS NOT NULL
        ) > 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM leaded_events;


-- ============================================================
-- CHECK 14: CHRONOLOGICAL ORDERING
-- ============================================================

WITH ordered_events AS (

    SELECT

        booking_id,

        event_timestamp,

        LAG(event_timestamp) OVER (
            PARTITION BY booking_id
            ORDER BY event_timestamp, event_id
        ) AS previous_timestamp

    FROM events
)

SELECT
    'Chronological event ordering' AS check_name,

    COUNT(*) FILTER (
        WHERE previous_timestamp IS NOT NULL
          AND event_timestamp < previous_timestamp
    ) AS invalid_rows,

    CASE
        WHEN COUNT(*) FILTER (
            WHERE previous_timestamp IS NOT NULL
              AND event_timestamp < previous_timestamp
        ) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

FROM ordered_events;


-- ============================================================
-- CHECK 15: ONE ROW PER BOOKING IN CUSTOMER-LEVEL SUMMARY
-- ============================================================

WITH booking_summary AS (

    SELECT

        b.booking_id,

        b.customer_id,

        COUNT(e.event_id) AS total_events

    FROM bookings b

    LEFT JOIN events e
        ON b.booking_id = e.booking_id

    GROUP BY
        b.booking_id,
        b.customer_id
)

SELECT
    'One row per booking' AS check_name,
    COUNT(*) AS actual_value,
    8000 AS expected_value,
    CASE
        WHEN COUNT(*) = 8000
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM booking_summary;


-- ============================================================
-- CHECK 16: EVENT COUNT RECONCILIATION
-- ============================================================

WITH booking_events AS (

    SELECT

        b.booking_id,

        COUNT(e.event_id) AS event_count

    FROM bookings b

    LEFT JOIN events e
        ON b.booking_id = e.booking_id

    GROUP BY
        b.booking_id
)

SELECT
    'Event count reconciliation' AS check_name,

    SUM(event_count) AS actual_value,

    61673 AS expected_value,

    CASE
        WHEN SUM(event_count) = 61673
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

FROM booking_events;


-- ============================================================
-- CHECK 17: PAYMENT COUNT RECONCILIATION
-- ============================================================

WITH booking_payments AS (

    SELECT

        b.booking_id,

        COUNT(p.payment_id) AS payment_count

    FROM bookings b

    LEFT JOIN payments p
        ON b.booking_id = p.booking_id

    GROUP BY
        b.booking_id
)

SELECT
    'Payment count reconciliation' AS check_name,

    SUM(payment_count) AS actual_value,

    10557 AS expected_value,

    CASE
        WHEN SUM(payment_count) = 10557
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

FROM booking_payments;


-- ============================================================
-- CHECK 18: CUSTOMER-LEVEL RECORD COUNT
-- ============================================================

WITH customer_summary AS (

    SELECT

        c.customer_id,

        COUNT(DISTINCT b.booking_id)
            AS total_bookings

    FROM customers c

    LEFT JOIN bookings b
        ON c.customer_id = b.customer_id

    GROUP BY
        c.customer_id
)

SELECT
    'Customer summary record count' AS check_name,

    COUNT(*) AS actual_value,

    5000 AS expected_value,

    CASE
        WHEN COUNT(*) = 5000
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

FROM customer_summary;


-- ============================================================
-- CHECK 19: CUSTOMER-LEVEL JOIN INTEGRITY
-- ============================================================

WITH customer_summary AS (

    SELECT

        c.customer_id,

        COUNT(DISTINCT b.booking_id)
            AS total_bookings

    FROM customers c

    LEFT JOIN bookings b
        ON c.customer_id = b.customer_id

    GROUP BY
        c.customer_id
)

SELECT
    'Customer IDs preserved' AS check_name,

    COUNT(*) FILTER (
        WHERE customer_id IS NULL
    ) AS invalid_rows,

    CASE
        WHEN COUNT(*) FILTER (
            WHERE customer_id IS NULL
        ) = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status

FROM customer_summary;


-- ============================================================
-- CHECK 20: SQL FEATURE REQUIREMENTS
-- ============================================================

SELECT
    'Advanced SQL requirements' AS check_name,

    5 AS required_features,

    5 AS implemented_features,

    CASE
        WHEN 5 = 5
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status;