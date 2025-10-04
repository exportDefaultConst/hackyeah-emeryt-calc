# Test API with PowerShell Invoke-RestMethod
# Make sure the API is running first: python run.py OR docker-compose up

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Testing Polish Pension Calculator API" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# API URL
$API_URL = "http://localhost:5000"

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
Write-Host "GET $API_URL/health" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$API_URL/health" -Method Get
    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host ""


# Test 2: Simple Pension Calculation (Minimal Data)
Write-Host "Test 2: Minimal Pension Calculation" -ForegroundColor Yellow
Write-Host "POST $API_URL/calculate_pension" -ForegroundColor Gray
Write-Host ""

$minimalData = @{
    user_data = @{
        age = 30
        gender = "female"
        gross_salary = 7000.0
        work_start_year = 2015
    }
}

try {
    $response = Invoke-RestMethod -Uri "$API_URL/calculate_pension" `
        -Method Post `
        -ContentType "application/json" `
        -Body ($minimalData | ConvertTo-Json -Depth 10)
    
    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host ""


# Test 3: Full Pension Calculation (All Data)
Write-Host "Test 3: Full Pension Calculation (All Fields)" -ForegroundColor Yellow
Write-Host "POST $API_URL/calculate_pension" -ForegroundColor Gray
Write-Host ""

$fullData = @{
    user_data = @{
        age = 35
        gender = "male"
        gross_salary = 8000.0
        work_start_year = 2010
        work_end_year = 2045
        industry = "IT"
        position = "Senior Developer"
        company = "Tech Company"
        zus_account_balance = 50000.0
        zus_subaccount_balance = 15000.0
        sick_leave_days_per_year = 5.0
    }
}

try {
    $response = Invoke-RestMethod -Uri "$API_URL/calculate_pension" `
        -Method Post `
        -ContentType "application/json" `
        -Body ($fullData | ConvertTo-Json -Depth 10)
    
    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host ""


# Test 4: Young Worker
Write-Host "Test 4: Young Worker (23 years old)" -ForegroundColor Yellow
Write-Host "POST $API_URL/calculate_pension" -ForegroundColor Gray
Write-Host ""

$youngWorker = @{
    user_data = @{
        age = 23
        gender = "male"
        gross_salary = 5500.0
        work_start_year = 2022
        industry = "Finance"
        position = "Junior Analyst"
    }
}

try {
    $response = Invoke-RestMethod -Uri "$API_URL/calculate_pension" `
        -Method Post `
        -ContentType "application/json" `
        -Body ($youngWorker | ConvertTo-Json -Depth 10)
    
    Write-Host "Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host ""

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Tests Complete!" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
