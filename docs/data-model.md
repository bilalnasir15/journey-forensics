# Journey Forensics Data Model

## Domain

Travel / Hospitality

## Entities

### Customer

Primary Key:
- customer_id

### Trip

Primary Key:
- trip_id

### Booking

Primary Key:
- booking_id

Foreign Keys:
- customer_id
- trip_id

### Payment

Primary Key:
- payment_id

Foreign Key:
- booking_id

### Complaint

Primary Key:
- complaint_id

Foreign Keys:
- customer_id
- booking_id

### Review

Primary Key:
- review_id

Foreign Keys:
- customer_id
- booking_id

### Event

Primary Key:
- event_id

Foreign Key:
- customer_id

## Core Customer Journey

Discovery
→ Booking
→ Payment
→ Trip
→ Complaint
→ Resolution
→ Review
→ Repeat Booking