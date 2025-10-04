# PowerShell Test Script for Pension Calculator API Endpoints
# Tests all endpoints with 3 different scenarios using Invoke-RestMethod

$baseUrl = "http://https://sym.packt.pl"
$headers = @{
    "Content-Type" = "application/json"
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  PENSION CALCULATOR API - ENDPOINT TESTS" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# ============================================
# TEST 1: Health Check Endpoint
# ============================================
Write-Host "TEST 1: Health Check Endpoint" -ForegroundColor Yellow
Write-Host "GET /api/health" -ForegroundColor Gray
Write-Host ""

$response = Invoke-RestMethod -Uri "$baseUrl/api/health" -Method Get
$response | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 2: Get ZUS Tables Endpoint
# ============================================
Write-Host "TEST 2: Get ZUS Tables Endpoint" -ForegroundColor Yellow
Write-Host "GET /zus_tables" -ForegroundColor Gray
Write-Host ""

$response = Invoke-RestMethod -Uri "$baseUrl/zus_tables" -Method Get
$response | ConvertTo-Json -Depth 5
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 3: Validate User Data - Case 1 (Valid Data)
# ============================================
Write-Host "TEST 3.1: Validate User Data - Valid Input" -ForegroundColor Yellow
Write-Host "POST /validate_user_data" -ForegroundColor Gray
Write-Host ""

$validData = @{
    user_data = @{
        age = 35
        gender = "male"
        gross_salary = 8000.0
        work_start_year = 2010
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$baseUrl/validate_user_data" -Method Post -Headers $headers -Body $validData
$response | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 3.2: Validate User Data - Case 2 (Invalid Age)
# ============================================
Write-Host "TEST 3.2: Validate User Data - Invalid Age" -ForegroundColor Yellow
Write-Host "POST /validate_user_data" -ForegroundColor Gray
Write-Host ""

$invalidAge = @{
    user_data = @{
        age = 15
        gender = "female"
        gross_salary = 5000.0
        work_start_year = 2020
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/validate_user_data" -Method Post -Headers $headers -Body $invalidAge
    $response | ConvertTo-Json -Depth 10
} catch {
    $_.ErrorDetails.Message | ConvertFrom-Json | ConvertTo-Json -Depth 10
}
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 3.3: Validate User Data - Case 3 (Invalid Gender & Salary)
# ============================================
Write-Host "TEST 3.3: Validate User Data - Multiple Errors" -ForegroundColor Yellow
Write-Host "POST /validate_user_data" -ForegroundColor Gray
Write-Host ""

$multipleErrors = @{
    user_data = @{
        age = 70
        gender = "X"
        gross_salary = -1000.0
        work_start_year = 2030
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/validate_user_data" -Method Post -Headers $headers -Body $multipleErrors
    $response | ConvertTo-Json -Depth 10
} catch {
    $_.ErrorDetails.Message | ConvertFrom-Json | ConvertTo-Json -Depth 10
}
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 4: Local Calculation - Case 1 (Young Professional)
# ============================================
Write-Host "TEST 4.1: Local Calculation - Young Professional (Male, 30)" -ForegroundColor Yellow
Write-Host "POST /api/calculate_pension_local" -ForegroundColor Gray
Write-Host ""

$youngPro = @{
    user_data = @{
        age = 30
        gender = "male"
        gross_salary = 10000.0
        work_start_year = 2017
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$baseUrl/api/calculate_pension_local" -Method Post -Headers $headers -Body $youngPro
Write-Host "Monthly Pension: $($response.monthly_pension) PLN" -ForegroundColor Green
$response | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 4.2: Local Calculation - Case 2 (Mid-Career with Balances)
# ============================================
Write-Host "TEST 4.2: Local Calculation - Mid-Career with ZUS Balances" -ForegroundColor Yellow
Write-Host "POST /api/calculate_pension_local" -ForegroundColor Gray
Write-Host ""

$midCareer = @{
    user_data = @{
        age = 45
        gender = "female"
        gross_salary = 7500.0
        work_start_year = 2000
        work_end_year = 2035
        zus_account_balance = 200000.0
        zus_subaccount_balance = 80000.0
        sick_leave_days_per_year = 10
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$baseUrl/api/calculate_pension_local" -Method Post -Headers $headers -Body $midCareer
Write-Host "Monthly Pension: $($response.monthly_pension) PLN" -ForegroundColor Green
$response | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 4.3: Local Calculation - Case 3 (Near Retirement with Custom Tables)
# ============================================
Write-Host "TEST 4.3: Local Calculation - Near Retirement with Custom Tables" -ForegroundColor Yellow
Write-Host "POST /api/calculate_pension_local" -ForegroundColor Gray
Write-Host ""

$nearRetirement = @{
    user_data = @{
        age = 58
        gender = "female"
        gross_salary = 6000.0
        work_start_year = 1990
        work_end_year = 2027
        zus_account_balance = 350000.0
        zus_subaccount_balance = 120000.0
    }
    official_tables = @{
        valorization_indices = @{
            "2024" = 1.1266
            "2025" = 1.0600
            "2026" = 1.0550
            "2027" = 1.0500
        }
        profitability_indices = @{
            "2024" = 1.0350
            "2025" = 1.0400
        }
    }
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "$baseUrl/api/calculate_pension_local" -Method Post -Headers $headers -Body $nearRetirement
Write-Host "Monthly Pension: $($response.monthly_pension) PLN" -ForegroundColor Green
$response | ConvertTo-Json -Depth 10
Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 5: FULL RESULT VERIFICATION - 3 Realistic Cases
# ============================================
Write-Host ""
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host "  TEST 5: FULL RESULT VERIFICATION" -ForegroundColor Magenta
Write-Host "  (Realistic scenarios with complete data)" -ForegroundColor Magenta
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host ""

# ============================================
# TEST 5.1: IT Specialist - High Earner, No Sick Leaves
# ============================================
Write-Host "TEST 5.1: IT Specialist - High Income Scenario" -ForegroundColor Yellow
Write-Host "POST /api/calculate_pension_local" -ForegroundColor Gray
Write-Host ""
Write-Host "Profile: 35-year-old male IT specialist" -ForegroundColor Cyan
Write-Host "  - Salary: 15,000 PLN/month" -ForegroundColor Cyan
Write-Host "  - Started: 2012 (13 years of work)" -ForegroundColor Cyan
Write-Host "  - Retirement: 2054 (at 65)" -ForegroundColor Cyan
Write-Host "  - No sick leaves, no existing ZUS balance" -ForegroundColor Cyan
Write-Host ""

$itSpecialist = @{
    user_data = @{
        age = 35
        gender = "male"
        gross_salary = 15000.0
        work_start_year = 2012
        work_end_year = 2054
        industry = "IT"
        position = "Senior Developer"
        sick_leave_days_per_year = 0
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/calculate_pension_local" -Method Post -Headers $headers -Body $itSpecialist
    Write-Host "Monthly Pension: $($response.monthly_pension) PLN" -ForegroundColor Green
    Write-Host "Replacement Rate: $($response.replacement_rate)%" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 5.2: Teacher - Average Income with Sick Leaves
# ============================================
Write-Host "TEST 5.2: Teacher - Average Income with Health Issues" -ForegroundColor Yellow
Write-Host "POST /api/calculate_pension_local" -ForegroundColor Gray
Write-Host ""
Write-Host "Profile: 42-year-old female teacher" -ForegroundColor Cyan
Write-Host "  - Salary: 6,500 PLN/month" -ForegroundColor Cyan
Write-Host "  - Started: 2005 (20 years of work)" -ForegroundColor Cyan
Write-Host "  - Retirement: 2043 (at 60)" -ForegroundColor Cyan
Write-Host "  - Sick leaves: 15 days/year average" -ForegroundColor Cyan
Write-Host "  - Existing ZUS balance: 120,000 PLN" -ForegroundColor Cyan
Write-Host ""

$teacher = @{
    user_data = @{
        age = 42
        gender = "female"
        gross_salary = 6500.0
        work_start_year = 2005
        work_end_year = 2043
        industry = "Education"
        position = "Teacher"
        zus_account_balance = 120000.0
        zus_subaccount_balance = 45000.0
        sick_leave_days_per_year = 15
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/calculate_pension_local" -Method Post -Headers $headers -Body $teacher
    Write-Host "Monthly Pension: $($response.monthly_pension) PLN" -ForegroundColor Green
    Write-Host "Replacement Rate: $($response.replacement_rate)%" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# TEST 5.3: Construction Worker - Low Income, Long Career
# ============================================
Write-Host "TEST 5.3: Construction Worker - Long Career, Lower Income" -ForegroundColor Yellow
Write-Host "POST /api/calculate_pension_local" -ForegroundColor Gray
Write-Host ""
Write-Host "Profile: 50-year-old male construction worker" -ForegroundColor Cyan
Write-Host "  - Salary: 5,200 PLN/month" -ForegroundColor Cyan
Write-Host "  - Started: 1993 (32 years of work)" -ForegroundColor Cyan
Write-Host "  - Retirement: 2040 (at 65)" -ForegroundColor Cyan
Write-Host "  - Sick leaves: 8 days/year average" -ForegroundColor Cyan
Write-Host "  - Existing ZUS balance: 180,000 PLN" -ForegroundColor Cyan
Write-Host ""

$constructionWorker = @{
    user_data = @{
        age = 50
        gender = "male"
        gross_salary = 5200.0
        work_start_year = 1993
        work_end_year = 2040
        industry = "Construction"
        position = "Skilled Worker"
        zus_account_balance = 180000.0
        zus_subaccount_balance = 65000.0
        sick_leave_days_per_year = 8
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/calculate_pension_local" -Method Post -Headers $headers -Body $constructionWorker
    Write-Host "Monthly Pension: $($response.monthly_pension) PLN" -ForegroundColor Green
    Write-Host "Replacement Rate: $($response.replacement_rate)%" -ForegroundColor Cyan
    Write-Host "Years of Contributions: $($response.years_of_contributions)" -ForegroundColor Magenta
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# ============================================
# SUMMARY
# ============================================
Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  ALL ENDPOINT TESTS COMPLETED" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tests executed:" -ForegroundColor Green
Write-Host "  1. Health Check (GET /api/health)" -ForegroundColor White
Write-Host "  2. Get ZUS Tables (GET /zus_tables)" -ForegroundColor White
Write-Host "  3. Validate User Data - 3 cases (POST /validate_user_data)" -ForegroundColor White
Write-Host "     - Valid data" -ForegroundColor Gray
Write-Host "     - Invalid age" -ForegroundColor Gray
Write-Host "     - Multiple errors" -ForegroundColor Gray
Write-Host "  4. Local Calculation - 3 cases (POST /api/calculate_pension_local)" -ForegroundColor White
Write-Host "     - Young professional" -ForegroundColor Gray
Write-Host "     - Mid-career with balances" -ForegroundColor Gray
Write-Host "     - Near retirement with custom tables" -ForegroundColor Gray
Write-Host "  5. Full Result Verification - 3 realistic cases" -ForegroundColor White
Write-Host "     - IT Specialist (high income, no sick leaves)" -ForegroundColor Gray
Write-Host "     - Teacher (average income, health issues)" -ForegroundColor Gray
Write-Host "     - Construction Worker (long career, lower income)" -ForegroundColor Gray
Write-Host ""
Write-Host "Total: 11 API calls across 4 endpoints" -ForegroundColor Green
Write-Host ""
Write-Host "Expected Results Summary:" -ForegroundColor Yellow
Write-Host "  - IT Specialist: ~8,000-10,000 PLN/month pension" -ForegroundColor White
Write-Host "  - Teacher: ~3,500-4,500 PLN/month pension" -ForegroundColor White
Write-Host "  - Construction Worker: ~2,500-3,500 PLN/month pension" -ForegroundColor White
Write-Host ""
