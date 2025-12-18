# GrihaStay API Test Collection

This file contains example API requests for testing all major endpoints.
Replace `YOUR_ACCESS_TOKEN` and UUIDs with actual values from responses.

## Variables
```
BASE_URL=http://localhost:8000/api
ACCESS_TOKEN=your-jwt-token-here
TENANT_ID=your-tenant-uuid
PROPERTY_ID=your-property-uuid
ROOM_TYPE_ID=your-room-type-uuid
```

---

## 1. Authentication

### Register Tenant
```bash
curl -X POST ${BASE_URL}/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Test Homestay",
    "contact_email": "contact@test.com",
    "user_name": "testadmin",
    "email": "admin@test.com",
    "password": "SecurePass123",
    "full_name": "Test Admin"
  }'
```

### Login
```bash
curl -X POST ${BASE_URL}/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "testadmin",
    "password": "SecurePass123"
  }'
```

### Refresh Token
```bash
curl -X POST ${BASE_URL}/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

---

## 2. Properties

### Create Property
```bash
curl -X POST ${BASE_URL}/properties/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Himalayan Paradise",
    "description": "Luxury homestay in the mountains",
    "address": "Pokhara, Lakeside",
    "currency": "NPR",
    "status": "LISTED",
    "lat": 28.2096,
    "lon": 83.9856
  }'
```

### List Properties
```bash
curl ${BASE_URL}/properties/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Get Single Property
```bash
curl ${BASE_URL}/properties/${PROPERTY_ID}/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Update Property
```bash
curl -X PATCH ${BASE_URL}/properties/${PROPERTY_ID}/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status": "LISTED"}'
```

---

## 3. Room Types

### Create Room Type
```bash
curl -X POST ${BASE_URL}/room-types/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "property": "'${PROPERTY_ID}'",
    "name": "Deluxe Room",
    "max_occupancy": 2,
    "default_base_price": 5000,
    "currency": "NPR",
    "description": "Comfortable room with city view"
  }'
```

### List Room Types
```bash
curl ${BASE_URL}/room-types/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Filter Room Types by Property
```bash
curl "${BASE_URL}/room-types/?property=${PROPERTY_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 4. Rooms

### Create Room
```bash
curl -X POST ${BASE_URL}/rooms/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "'${ROOM_TYPE_ID}'",
    "room_number": "101",
    "status": "AVAILABLE"
  }'
```

### List Rooms
```bash
curl ${BASE_URL}/rooms/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 5. Bookings

### Create Booking
```bash
curl -X POST ${BASE_URL}/bookings/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "property": "'${PROPERTY_ID}'",
    "room_type": "'${ROOM_TYPE_ID}'",
    "checkin": "2025-01-20",
    "checkout": "2025-01-22",
    "guests_count": 2,
    "total_amount": 10000,
    "currency": "NPR",
    "status": "CONFIRMED"
  }'
```

### List Bookings
```bash
curl ${BASE_URL}/bookings/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Filter Bookings
```bash
curl "${BASE_URL}/bookings/?status=CONFIRMED&ordering=-checkin" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Confirm Booking
```bash
curl -X POST ${BASE_URL}/bookings/${BOOKING_ID}/confirm/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Cancel Booking
```bash
curl -X POST ${BASE_URL}/bookings/${BOOKING_ID}/cancel/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Check-in
```bash
curl -X POST ${BASE_URL}/bookings/${BOOKING_ID}/checkin/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Check-out
```bash
curl -X POST ${BASE_URL}/bookings/${BOOKING_ID}/checkout/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 6. Guests

### Create Guest
```bash
curl -X POST ${BASE_URL}/guests/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+977-9876543210",
    "nationality": "USA"
  }'
```

### List Guests
```bash
curl ${BASE_URL}/guests/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Search Guests
```bash
curl "${BASE_URL}/guests/?search=john" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 7. Rate Plans

### Create Rate Plan
```bash
curl -X POST ${BASE_URL}/rate-plans/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "property": "'${PROPERTY_ID}'",
    "room_type": "'${ROOM_TYPE_ID}'",
    "name": "Weekend Rate",
    "base_price": 6000,
    "currency": "NPR",
    "active": true
  }'
```

### List Rate Plans
```bash
curl ${BASE_URL}/rate-plans/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 8. Inventory

### Create/Update Inventory
```bash
curl -X POST ${BASE_URL}/inventory/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "'${ROOM_TYPE_ID}'",
    "dt": "2025-01-15",
    "available_count": 5,
    "blocked_count": 0
  }'
```

### List Inventory
```bash
curl "${BASE_URL}/inventory/?room_type=${ROOM_TYPE_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 9. Users

### Create User (Owner only)
```bash
curl -X POST ${BASE_URL}/users/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "receptionist1",
    "email": "receptionist@test.com",
    "password": "Recept123",
    "full_name": "Jane Receptionist",
    "role": "RECEPTIONIST"
  }'
```

### List Users
```bash
curl ${BASE_URL}/users/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### Get Current User
```bash
curl ${BASE_URL}/users/me/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 10. Location Data

### List Countries
```bash
curl ${BASE_URL}/countries/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### List States
```bash
curl ${BASE_URL}/states/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### List Districts
```bash
curl ${BASE_URL}/districts/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

### List Cities
```bash
curl ${BASE_URL}/cities/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 11. Communities

### Create Community
```bash
curl -X POST ${BASE_URL}/communities/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lakeside Community",
    "description": "Tourist area near the lake"
  }'
```

### List Communities
```bash
curl ${BASE_URL}/communities/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 12. Amenities

### Create Amenity
```bash
curl -X POST ${BASE_URL}/amenities/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WiFi",
    "description": "High-speed internet"
  }'
```

### List Amenities
```bash
curl ${BASE_URL}/amenities/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 13. Payments

### Create Payment
```bash
curl -X POST ${BASE_URL}/payments/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "booking": "'${BOOKING_ID}'",
    "method": "GATEWAY",
    "amount": 10000,
    "currency": "NPR",
    "status": "PAID",
    "transaction_id": "TXN123456"
  }'
```

### List Payments
```bash
curl ${BASE_URL}/payments/ \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

---

## 14. Health Check

### Check API Status
```bash
curl ${BASE_URL}/health/
```

---

## Tips

1. **Save tokens**: After login, save the access token to use in subsequent requests
2. **Save UUIDs**: Save returned IDs to use in related requests
3. **Pagination**: Add `?page=2&page_size=10` to list endpoints
4. **Filtering**: Use `?field=value` for exact matches
5. **Search**: Use `?search=keyword` for text search
6. **Ordering**: Use `?ordering=-created_at` for sorting (- for descending)

## Example Workflow

1. Register tenant → Get access token
2. Create property → Get property ID
3. Create room type → Get room type ID
4. Create rooms → Get room IDs
5. Create guest → Get guest ID
6. Create booking → Get booking ID
7. Create payment → Complete transaction
