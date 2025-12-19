# GrihaStay - HomeStay Management Backend

A comprehensive Django REST Framework backend for managing homestay properties with multi-tenancy support, JWT authentication, and PostgreSQL/PostGIS database.

## Features

### Core Functionality
- **Multi-Tenancy**: Each tenant represents a separate homestay owner or company
- **Authentication & Authorization**: 
  - JWT-based authentication
  - Role-based access control (Owner, Manager, Receptionist, Housekeeping, Auditor)
  - First user registration automatically becomes Tenant Admin
- **Complete CRUD APIs** for all entities:
  - Properties, Room Types, Rooms, Bookings
  - Rate Plans, Inventory Management
  - Guests, Payments, Invoices
  - Location data (Countries, States, Districts, Cities, Communities)

### Technical Features
- Django 4.2 with Django REST Framework
- PostgreSQL with PostGIS for geospatial data
- Docker containerization
- CORS enabled for React frontend integration
- Comprehensive filtering, searching, and pagination
- Automated migrations and database initialization

## Project Structure

```
grihaStayPro/
├── backend/
│   ├── config/              # Django settings and configuration
│   │   ├── settings.py      # Main settings with JWT, CORS, multi-tenancy
│   │   ├── urls.py          # Root URL configuration
│   │   ├── wsgi.py          # WSGI application
│   │   └── asgi.py          # ASGI application
│   ├── core/                # Main application
│   │   ├── models.py        # All database models
│   │   ├── serializers.py   # DRF serializers
│   │   ├── viewsets.py      # DRF viewsets
│   │   ├── views.py         # Authentication views
│   │   ├── permissions.py   # Custom permissions
│   │   ├── middleware.py    # Tenant middleware
│   │   ├── urls.py          # API routes
│   │   └── admin.py         # Django admin configuration
│   ├── manage.py            # Django management script
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Docker configuration
│   └── entrypoint.sh        # Docker entrypoint script
├── docker-compose.yml       # Docker Compose configuration
├── GrihaStaySQL.sql        # Database schema
├── .env                    # Environment variables
└── README.md               # This file
```

## Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.11+ for local development

## Quick Start with Docker

### 1. Clone the repository and navigate to the project directory

```bash
cd /home/shree/grihaStayPro
```

### 2. Set up environment variables and docker file

Copy the example environment file and compose file :

```bash
cp .env.example .env
cp docker-compose.example.yml docker-compose.yml
```

Edit `.env` if needed (default values should work for development).

### 3. Build and run with Docker Compose

```bash
docker-compose up --build
```

This will:
- Start PostgreSQL with PostGIS extension
- Initialize the database with the schema from `GrihaStaySQL.sql`
- Run Django migrations
- Start the Django development server on `http://localhost:8000`

### 4. Access the application

- **API Base URL**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/

## API Documentation

### Authentication Endpoints

#### Register New Tenant (First Registration)
```bash
POST /api/auth/register/
Content-Type: application/json

{
  "tenant_name": "My Homestay",
  "contact_email": "contact@example.com",
  "contact_phone": "+1234567890",
  "registration_number": "REG123",
  "currency": "NPR",
  "timezone": "Asia/Kathmandu",
  "user_name": "admin",
  "email": "admin@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "mobile_number": "+1234567890"
}
```

Response:
```json
{
  "message": "Tenant and admin user created successfully",
  "tenant": { ... },
  "user": { ... },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

#### Login
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "user_name": "admin",
  "password": "securepassword"
}
```

Response:
```json
{
  "refresh": "...",
  "access": "...",
  "user": { ... },
  "tenant": { ... }
}
```

#### Refresh Token
```bash
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "your-refresh-token"
}
```

### Using the API with JWT

Include the access token in the Authorization header:

```bash
Authorization: Bearer <your-access-token>
```

Example:
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  http://localhost:8000/api/properties/
```

### Available API Endpoints

All endpoints support standard REST operations (GET, POST, PUT, PATCH, DELETE) where applicable:

#### Location & Community
- `/api/countries/` - Country management
- `/api/states/` - State management
- `/api/districts/` - District management
- `/api/municipalities/` - Municipality management
- `/api/cities/` - City management
- `/api/communities/` - Community management
- `/api/community-media/` - Community media files

#### Tenant & Users
- `/api/tenants/` - Tenant management (owner only)
- `/api/users/` - User management within tenant
- `/api/users/me/` - Get current user info

#### Properties
- `/api/property-types/` - Property type categories
- `/api/amenities/` - Available amenities
- `/api/properties/` - Property CRUD operations
- `/api/room-types/` - Room type management
- `/api/rooms/` - Individual room management
- `/api/room-images/` - Room images

#### Rate Plans & Inventory
- `/api/rate-plans/` - Rate plan management
- `/api/rate-plan-rules/` - Rate plan rules (seasonal, occupancy-based)
- `/api/inventory/` - Daily inventory management
- `/api/channel-allocations/` - Channel distribution allocations

#### Bookings & Guests
- `/api/guests/` - Guest profiles
- `/api/tenant-guest-profiles/` - Tenant-specific guest data
- `/api/bookings/` - Booking management
  - `POST /api/bookings/{id}/confirm/` - Confirm booking
  - `POST /api/bookings/{id}/cancel/` - Cancel booking
  - `POST /api/bookings/{id}/checkin/` - Check-in guest
  - `POST /api/bookings/{id}/checkout/` - Check-out guest
- `/api/booking-items/` - Booking line items
- `/api/booking-guest-info/` - Guest information for bookings

#### Payments & Financial
- `/api/payments/` - Payment tracking
- `/api/invoices/` - Invoice management
- `/api/payouts/` - Payout management (owner only)

#### Admin & Monitoring
- `/api/webhooks/` - Webhook registrations (owner only)
- `/api/audit-logs/` - Audit log viewing (owner/manager only)

### Query Parameters

Most list endpoints support:
- **Filtering**: `?status=LISTED&property_type=<uuid>`
- **Search**: `?search=keyword`
- **Ordering**: `?ordering=-created_at`
- **Pagination**: `?page=2&page_size=20`

Example:
```bash
GET /api/bookings/?status=CONFIRMED&ordering=-checkin&page=1
```

## Role-Based Permissions

### OWNER (Tenant Admin)
- Full access to all tenant data
- Can create/manage users
- Can manage webhooks and view audit logs
- Can manage payouts

### MANAGER
- Can view audit logs
- Can manage properties, rooms, bookings
- Cannot create users or manage tenant settings

### RECEPTIONIST
- Can manage bookings
- Can view properties and rooms
- Limited administrative access

### HOUSEKEEPING
- Can view room assignments
- Can update room status
- Limited to operational tasks

### AUDITOR
- Read-only access to audit logs
- Can view financial reports

## Multi-Tenancy

The system implements row-level multi-tenancy:

1. **Tenant Isolation**: Each API request is scoped to the authenticated user's tenant
2. **Automatic Filtering**: All queries automatically filter by tenant
3. **JWT Claims**: Tenant ID is embedded in JWT tokens
4. **Middleware**: Custom middleware sets tenant context for each request

## Database Schema

The database schema is defined in `GrihaStaySQL.sql` and includes:

- **39+ tables** covering all aspects of homestay management
- **PostgreSQL enums** for status types
- **PostGIS** for geospatial data (property locations)
- **Triggers** for automatic timestamp updates
- **Constraints** for data integrity

Key entities:
- Tenants, Users, Properties, Rooms, Bookings
- Rate Plans, Inventory, Payments, Invoices
- Communities, Amenities, Guests
- Audit Logs, Webhooks, API Keys

## Local Development (Without Docker)

### 1. Set up Python environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up PostgreSQL

Install PostgreSQL with PostGIS extension and create database:

```bash
createdb grihastay
psql -d grihastay -c "CREATE EXTENSION postgis;"
psql -d grihastay -f ../GrihaStaySQL.sql
```

### 3. Configure environment

```bash
export POSTGRES_HOST=localhost
export POSTGRES_DB=grihastay
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
```

### 4. Run migrations and start server

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Testing the API

### Using curl

```bash
# Register a tenant
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Test Homestay",
    "user_name": "testadmin",
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test Admin"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "testadmin",
    "password": "testpass123"
  }'

# Use the API (replace TOKEN with access token from login)
curl http://localhost:8000/api/properties/ \
  -H "Authorization: Bearer TOKEN"
```

### Using Postman or Insomnia

1. Import the API endpoints
2. Set up environment variables for base URL and tokens
3. Use Bearer Token authentication
4. Test all CRUD operations

## Production Deployment

### Security Checklist

1. **Change SECRET_KEY**: Generate a strong secret key
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. **Set DEBUG=False** in production

3. **Configure ALLOWED_HOSTS**: Set to your domain
   ```
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

4. **Use strong database password**

5. **Configure CORS_ALLOWED_ORIGINS**: Set specific frontend URLs
   ```
   CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```

6. **Use HTTPS**: Configure SSL/TLS certificates

7. **Set up proper database backups**

8. **Use environment-specific settings**

### Docker Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:15-3.3
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    restart: always

  backend:
    build: ./backend
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_HOST=db
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS}
    depends_on:
      - db
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - backend
    restart: always

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

Add gunicorn to requirements.txt:
```
gunicorn==21.2.0
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs db

# Restart services
docker-compose restart
```

### Migration Issues

```bash
# Access Django container
docker-compose exec backend bash

# Run migrations manually
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### JWT Token Issues

- Ensure token is included in Authorization header
- Check token expiration (default: 1 hour for access token)
- Use refresh token to get new access token

## Support and Contributing

For issues, questions, or contributions, please contact the development team.

## License

Proprietary - All rights reserved

---

**GrihaStay Backend v1.0** - Built with Django REST Framework
# homestaybackend
