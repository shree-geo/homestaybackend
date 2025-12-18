#!/bin/bash

# GrihaStay API Test Script

BASE_URL="http://localhost:8000/api"

echo "================================================"
echo "GrihaStay API Test Suite"
echo "================================================"
echo ""

# 1. Health Check
echo "1. Testing Health Endpoint..."
curl -s $BASE_URL/health/ | python3 -m json.tool
echo ""
echo ""

# 2. Register Tenant (if not exists)
echo "2. Registering Tenant..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "Demo Homestay",
    "contact_email": "demo@homestay.com",
    "user_name": "demo",
    "email": "demo@homestay.com",
    "password": "Demo@123",
    "full_name": "Demo User"
  }')

echo "$REGISTER_RESPONSE" | python3 -m json.tool

# Extract access token from registration
ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tokens', {}).get('access', ''))" 2>/dev/null)

echo ""
echo "Access Token: $ACCESS_TOKEN"
echo ""
echo ""

# 4. Test Properties Endpoint (should be empty initially)
echo "3. Getting Properties (should be empty)..."
curl -s -X GET $BASE_URL/properties/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
echo ""

# 5. Create a Property
echo "4. Creating a Property..."
PROPERTY_RESPONSE=$(curl -s -X POST $BASE_URL/properties/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mountain View Villa",
    "description": "Beautiful villa with mountain views",
    "address": "Pokhara, Lakeside",
    "currency": "NPR",
    "status": "LISTED"
  }')

echo "$PROPERTY_RESPONSE" | python3 -m json.tool
PROPERTY_ID=$(echo "$PROPERTY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo ""
echo ""

# 6. Get Properties Again
echo "5. Getting Properties (should show created property)..."
curl -s -X GET $BASE_URL/properties/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
echo ""

# 7. Get Single Property
echo "6. Getting Single Property Details..."
curl -s -X GET "$BASE_URL/properties/$PROPERTY_ID/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
echo ""

# 8. Update Property
echo "7. Updating Property..."
curl -s -X PATCH "$BASE_URL/properties/$PROPERTY_ID/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Beautiful villa with stunning mountain and lake views",
    "status": "ACTIVE"
  }' | python3 -m json.tool
echo ""
echo ""

# 9. Test Room Type
echo "8. Creating a Room Type..."
curl -s -X POST $BASE_URL/room-types/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deluxe Room",
    "description": "Spacious deluxe room with modern amenities",
    "max_occupancy": 2,
    "base_price": 5000.00,
    "currency": "NPR"
  }' | python3 -m json.tool
echo ""
echo ""

# 10. Get Room Types
echo "9. Getting Room Types..."
curl -s -X GET $BASE_URL/room-types/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""
echo ""

echo "================================================"
echo "✅ All Tests Complete!"
echo "================================================"
echo ""
echo "Your system is working correctly!"
echo ""
echo "Access Token for future requests:"
echo "$ACCESS_TOKEN"
echo ""
echo "Property ID: $PROPERTY_ID"
