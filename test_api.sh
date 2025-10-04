#!/bin/bash
# Test API with curl commands
# Make sure the API is running first: python run.py OR docker-compose up

echo "============================================================"
echo "Testing Polish Pension Calculator API"
echo "============================================================"
echo ""

API_URL="http://localhost:5000"

# Test 1: Health Check
echo "Test 1: Health Check"
echo "GET $API_URL/health"
echo ""
curl -X GET "$API_URL/health"
echo ""
echo ""

# Test 2: Simple Pension Calculation (Minimal Data)
echo "Test 2: Minimal Pension Calculation"
echo "POST $API_URL/calculate_pension"
echo ""
curl -X POST "$API_URL/calculate_pension" \
    -H "Content-Type: application/json" \
    -d '{
        "user_data": {
            "age": 30,
            "gender": "female",
            "gross_salary": 7000.0,
            "work_start_year": 2015
        }
    }'
echo ""
echo ""

# Test 3: Full Pension Calculation (All Data)
echo "Test 3: Full Pension Calculation (All Fields)"
echo "POST $API_URL/calculate_pension"
echo ""
curl -X POST "$API_URL/calculate_pension" \
    -H "Content-Type: application/json" \
    -d '{
        "user_data": {
            "age": 35,
            "gender": "male",
            "gross_salary": 8000.0,
            "work_start_year": 2010,
            "work_end_year": 2045,
            "industry": "IT",
            "position": "Senior Developer",
            "company": "Tech Company",
            "zus_account_balance": 50000.0,
            "zus_subaccount_balance": 15000.0,
            "sick_leave_days_per_year": 5.0
        }
    }'
echo ""
echo ""

# Test 4: Young Worker
echo "Test 4: Young Worker (23 years old)"
echo "POST $API_URL/calculate_pension"
echo ""
curl -X POST "$API_URL/calculate_pension" \
    -H "Content-Type: application/json" \
    -d '{
        "user_data": {
            "age": 23,
            "gender": "male",
            "gross_salary": 5500.0,
            "work_start_year": 2022,
            "industry": "Finance",
            "position": "Junior Analyst"
        }
    }'
echo ""
echo ""

echo "============================================================"
echo "Tests Complete!"
echo "============================================================"
