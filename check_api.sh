#!/bin/bash
# Quick API Diagnostics Script
# Run this to check if all endpoints are working

API_URL="https://chemical-backend-production-dd2c.up.railway.app"
TOKEN="$1"

if [ -z "$TOKEN" ]; then
    echo "Usage: bash check_api.sh <your_jwt_token>"
    echo ""
    echo "Example:"
    echo "  bash check_api.sh eyJhbGciOiJIUzI1NiI..."
    exit 1
fi

echo "🔍 Checking API Endpoints..."
echo "Backend: $API_URL"
echo ""

# Health Check
echo "✅ Health Check:"
curl -s -X GET "$API_URL/api/health/" | jq .
echo ""

# History
echo "✅ History (First 2):"
curl -s -X GET "$API_URL/api/history/" \
  -H "Authorization: Bearer $TOKEN" | jq '.history | .[0:2]'
echo ""

# Get First Dataset
echo "✅ First Dataset Details:"
curl -s -X GET "$API_URL/api/dataset/1/" \
  -H "Authorization: Bearer $TOKEN" | jq '.summary'
echo ""

# Test CSV Export (First 100 bytes)
echo "✅ CSV Export (Preview):"
curl -s -X GET "$API_URL/api/export/csv/1/" \
  -H "Authorization: Bearer $TOKEN" | head -c 200
echo ""
echo ""

# Summary
echo "🎯 Summary:"
echo "If all calls returned data above, your API is working!"
echo ""
echo "To debug in browser:"
echo "1. Open DevTools: F12"
echo "2. Go to Console tab"
echo "3. Click View Analysis button"
echo "4. Check console for logs and errors"
