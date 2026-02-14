#!/bin/bash

# Keycloak Auth Test Script

echo "=== Step 1: Get Keycloak Admin Token ==="
ADMIN_TOKEN=$(curl -s -X POST \
  "http://localhost:18080/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" \
  -d "grant_type=password" | jq -r '.access_token')

if [ "$ADMIN_TOKEN" = "null" ] || [ -z "$ADMIN_TOKEN" ]; then
  echo "Failed to get admin token"
  exit 1
fi

echo "Admin token: ${ADMIN_TOKEN:0:20}..."

echo ""
echo "=== Step 2: Create test user ==="
curl -s -X POST \
  "http://localhost:18080/admin/realms/control-plane/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "firstName": "Test",
    "lastName": "User",
    "email": "testuser@example.com",
    "enabled": true,
    "credentials": [{
      "type": "password",
      "value": "testuser123",
      "temporary": false
    }],
    "attributes": {
      "org_id": ["123e4567-e89b-12d3-a456-426614174000"]
    }
  }'

echo ""
echo ""
echo "=== Step 3: Get token as test user ==="
USER_TOKEN=$(curl -s -X POST \
  "http://localhost:18080/realms/control-plane/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=control-plane-client" \
  -d "client_secret=6iglxYwYReZZveuBZbIVW4OucEXhojvp" \
  -d "username=testuser" \
  -d "password=testuser123" \
  -d "grant_type=password" | jq -r '.access_token')

echo "User token: ${USER_TOKEN:0:20}..."
echo ""
echo "Full token response:"
curl -s -X POST \
  "http://localhost:18080/realms/control-plane/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=control-plane-client" \
  -d "client_secret=6iglxYwYReZZveuBZbIVW4OucEXhojvp" \
  -d "username=testuser" \
  -d "password=testuser123" \
  -d "grant_type=password" | jq '.'

echo ""
echo "=== Step 4: Decode token (verify org_id claim) ==="
curl -s -X POST \
  "http://localhost:18080/realms/control-plane/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=control-plane-client" \
  -d "client_secret=6iglxYwYReZZveuBZbIVW4OucEXhojvp" \
  -d "username=testuser" \
  -d "password=testuser123" \
  -d "grant_type=password" | jq -r '.access_token' | jq -R 'split(".") | .[1]' | jq -R '@base64d' | jq '.'

echo ""
echo "=== Step 5: Test backend /me endpoint ==="
curl -s -X GET \
  "http://localhost:8000/v1/auth/me" \
  -H "Authorization: Bearer $USER_TOKEN" | jq '.'

echo ""
echo "=== Done ==="
