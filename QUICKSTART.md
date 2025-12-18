# GrihaStay Backend - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Application
```bash
cd /home/shree/grihaStayPro
docker-compose up --build
```

Wait for the services to start. You should see:
- ✅ PostgreSQL database started
- ✅ Database initialized with schema
- ✅ Django migrations applied
- ✅ Server running at http://localhost:8000

### Step 2: Register Your First Tenant (Homestay Owner)

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Sunshine Homestay",
    "contact_email": "info@sunshine.com",
    "contact_phone": "+977-9876543210",
    "currency": "NPR",
    "timezone": "Asia/Kathmandu",
    "user_name": "admin",
    "email": "admin@sunshine.com",
    "password": "Admin@123",
    "full_name": "John Smith",
    "mobile_number": "+977-9876543210"
  }'
```

**Response:** You'll receive JWT tokens and tenant/user information.

### Step 3: Login and Get Access Token

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "admin",
    "password": "Admin@123"
  }'
```

**Save the `access` token from the response!**

---

## 📝 Test the API

### Create a Property

```bash
curl -X POST http://localhost:8000/api/properties/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Mountain View Villa",
    "description": "Beautiful villa with mountain views",
    "address": "Pokhara, Nepal",
    "currency": "NPR",
    "status": "LISTED"
  }'
```

### List All Properties

```bash
curl http://localhost:8000/api/properties/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create a Room Type

```bash
curl -X POST http://localhost:8000/api/room-types/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "property": "PROPERTY_UUID_FROM_ABOVE",
    "name": "Deluxe Double Room",
    "max_occupancy": 2,
    "default_base_price": 5000,
    "currency": "NPR",
    "description": "Spacious double room with mountain view"
  }'
```

### Create a Booking

```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "property": "PROPERTY_UUID",
    "room_type": "ROOM_TYPE_UUID",
    "checkin": "2025-01-15",
    "checkout": "2025-01-17",
    "guests_count": 2,
    "total_amount": 10000,
    "currency": "NPR"
  }'
```

---

## 🔧 Useful Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Database only
docker-compose logs -f db
```

### Stop Services
```bash
docker-compose down
```

### Reset Database (WARNING: Deletes all data)
```bash
docker-compose down -v
docker-compose up --build
```

### Access Django Shell
```bash
docker-compose exec backend python manage.py shell
```

### Create Django Superuser for Admin Panel
```bash
docker-compose exec backend python manage.py createsuperuser
```

### Access Admin Panel
Open: http://localhost:8000/admin/

---

## 📚 API Endpoints Reference

### Authentication
- `POST /api/auth/register/` - Register new tenant with admin user
- `POST /api/auth/login/` - Login and get JWT tokens
- `POST /api/auth/token/refresh/` - Refresh access token

### Core Resources
- `/api/properties/` - Property management
- `/api/room-types/` - Room type management
- `/api/rooms/` - Individual room management
- `/api/bookings/` - Booking management
- `/api/guests/` - Guest management
- `/api/payments/` - Payment tracking
- `/api/rate-plans/` - Rate plan management
- `/api/inventory/` - Inventory management

### User Management
- `/api/users/` - Manage users in your tenant
- `/api/users/me/` - Get current user info

### Reference Data
- `/api/countries/`, `/api/states/`, `/api/districts/`, `/api/cities/`
- `/api/communities/` - Community/area listings
- `/api/amenities/` - Available amenities
- `/api/property-types/` - Property categories

---

## 🎯 Next Steps

1. **Explore the API**: Use Postman or Insomnia to test all endpoints
2. **Create Test Data**: Add properties, room types, and test bookings
3. **Integrate Frontend**: Use the JWT tokens to connect your React app
4. **Customize**: Modify models, add business logic, create reports

---

## ❓ Troubleshooting

**Database connection failed?**
- Wait a few seconds for PostgreSQL to fully start
- Check logs: `docker-compose logs db`

**Permission denied on entrypoint.sh?**
```bash
chmod +x backend/entrypoint.sh
```

**Port already in use?**
- Stop other services using port 8000 or 5432
- Or modify ports in docker-compose.yml

**Need to rebuild?**
```bash
docker-compose down
docker-compose up --build
```

---

## 📖 Full Documentation

See [README.md](README.md) for complete documentation including:
- Detailed API reference
- Security configuration
- Production deployment guide
- Database schema details
- Multi-tenancy architecture

---

**Happy Building! 🏠**
