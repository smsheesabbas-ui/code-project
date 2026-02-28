# Railway Deployment Script
param(
    [Parameter(Mandatory=$true)]
    [string]$RailwayToken,
    
    [Parameter(Mandatory=$true)]
    [string]$GeminiApiKey,
    
    [Parameter()]
    [string]$GitHubRepo = "smsheesabbas-ui/code-project"
)

$headers = @{
    "Authorization" = "Bearer $RailwayToken"
    "Content-Type" = "application/json"
}

Write-Host "🚀 Starting Railway Deployment for CashFlow AI..." -ForegroundColor Green

# Create project
$projectBody = @{
    query = "mutation { projectCreate(input: {name: `"CashFlow AI`"}) { id name } }"
} | ConvertTo-Json -Depth 10

$project = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $projectBody
$projectId = $project.data.projectCreate.id
Write-Host "✅ Project created: $($project.data.projectCreate.name)" -ForegroundColor Green

# Add backend service
$backendBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"backend`", source: {repo: `"$GitHubRepo`", branch: `"master`", root: `"backend`", builder: `"DOCKERFILE`"}}) { id name } }"
} | ConvertTo-Json -Depth 10

$backend = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $backendBody
$backendId = $backend.data.serviceCreate.id
Write-Host "✅ Backend service created" -ForegroundColor Green

# Add frontend service
$frontendBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"frontend`", source: {repo: `"$GitHubRepo`", branch: `"master`", root: `"frontend`", builder: `"NIXPACKS`"}}) { id name } }"
} | ConvertTo-Json -Depth 10

$frontend = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $frontendBody
$frontendId = $frontend.data.serviceCreate.id
Write-Host "✅ Frontend service created" -ForegroundColor Green

# Add MongoDB
$mongoBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"mongodb`", source: {image: `"mongo:latest`"}}) { id name } }"
} | ConvertTo-Json -Depth 10

$mongo = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $mongoBody
$mongoId = $mongo.data.serviceCreate.id
Write-Host "✅ MongoDB created" -ForegroundColor Green

# Add Redis
$redisBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"redis`", source: {image: `"redis:latest`"}}) { id name } }"
} | ConvertTo-Json -Depth 10

$redis = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $redisBody
$redisId = $redis.data.serviceCreate.id
Write-Host "✅ Redis created" -ForegroundColor Green

# Set environment variables
$secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$envBody = @{
    query = "mutation { environmentVariableUpsert(serviceId: `"$backendId`", input: [{key: `"GEMINI_API_KEY`", value: `"$GeminiApiKey`"}, {key: `"SECRET_KEY`", value: `"$secretKey`"}]) { key value } }"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $envBody
Write-Host "✅ Environment variables set" -ForegroundColor Green

# Deploy services
Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body (@{query = "mutation { serviceDeploy(serviceId: `"$backendId`") { id } }" | ConvertTo-Json -Depth 10)
Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body (@{query = "mutation { serviceDeploy(serviceId: `"$frontendId`") { id } }" | ConvertTo-Json -Depth 10)

Write-Host "🚀 Deployment started! Check Railway dashboard for status." -ForegroundColor Green
Write-Host "🌐 Your app will be live at: https://cashflow-ai.up.railway.app" -ForegroundColor Cyan
