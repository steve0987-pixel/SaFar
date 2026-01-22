# API Testing Guide

## Using curl

### 1. Health Check
```bash
curl http://localhost:3000/api/health
```

### 2. Get All Places
```bash
curl http://localhost:3000/api/places
```

### 3. Get Hotels with Filters
```bash
# All hotels
curl http://localhost:3000/api/hotels

# Filter by price range
curl "http://localhost:3000/api/hotels?minPrice=50&maxPrice=150"

# Filter by stars
curl "http://localhost:3000/api/hotels?stars=4"
```

### 4. Get Restaurants
```bash
# All restaurants
curl http://localhost:3000/api/restaurants

# Filter by type
curl "http://localhost:3000/api/restaurants?type=Traditional"
```

### 5. User Registration
```bash
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123"
  }'
```

### 6. User Login
```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

### 7. Create Itinerary
```bash
curl -X POST http://localhost:3000/api/itineraries \
  -H "Content-Type: application/json" \
  -d '{
    "days": 5,
    "budget": 100,
    "interests": ["History", "Food", "Culture"],
    "travelStyle": "Couple",
    "activityLevel": "Moderate"
  }'
```

### 8. Get User Itineraries
```bash
# Replace USER_ID with actual user ID
curl "http://localhost:3000/api/itineraries?userId=USER_ID"
```

## Using Postman

1. Download Postman: https://www.postman.com/downloads/
2. Create new collection "Safar API"
3. Add requests for each endpoint above
4. Set base URL variable: `{{baseUrl}}` = `http://localhost:3000/api`

## Using Thunder Client (VS Code Extension)

1. Install Thunder Client extension
2. Create new collection
3. Add requests with examples above

## Expected Responses

### Success Response (200/201)
```json
{
  "_id": "123abc",
  "name": "Registan Square",
  "rating": 4.9,
  ...
}
```

### Error Response (400/401/404/500)
```json
{
  "error": "Error message here"
}
```

## Authentication

For protected routes (in future):
```bash
curl http://localhost:3000/api/protected-route \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```
