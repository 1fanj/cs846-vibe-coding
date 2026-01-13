#!/usr/bin/env bash
# Example curl commands for the Vibe API (assumes server at http://localhost:8000)

BASE=http://localhost:8000

echo "Register a user:"
curl -s -X POST "$BASE/register" -H "Content-Type: application/json" -d '{"username":"alice","display_name":"Alice","password":"secret"}' | jq

echo "\nLogin to get token (form-data):"
LOGIN_RESP=$(curl -s -X POST "$BASE/token" -F "username=alice" -F "password=secret")
echo "$LOGIN_RESP" | (jq . || python3 -c 'import sys,json;print(json.load(sys.stdin))')

# extract access_token (try jq, fallback to python)
TOKEN=$(echo "$LOGIN_RESP" | jq -r .access_token 2>/dev/null || python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
	echo "ERROR: could not extract access token; aborting authenticated calls"
	exit 1
fi

echo "\nCreate a post:"
curl -s -X POST "$BASE/posts" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"content":"Hello from curl!"}' | (jq . || cat)

echo "\nGet global feed:"
curl -s "$BASE/feed" | (jq . || cat)

echo "\nLike a post (post id 1):"
curl -s -X POST "$BASE/posts/1/like" -H "Authorization: Bearer $TOKEN" | (jq . || cat)

echo "\nView profile:"
curl -s "$BASE/users/alice" | (jq . || cat)
