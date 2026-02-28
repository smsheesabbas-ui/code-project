# Railway Auto-Deploy Script
# Run this in PowerShell with your Railway token

# Set your Railway API token
$RAILWAY_TOKEN = "YOUR_RAILWAY_TOKEN_HERE"

# Headers for API requests
$headers = @{
    "Authorization" = "Bearer $RAILWAY_TOKEN"
    "Content-Type" = "application/json"
}

Write-Host "🚀 Starting Railway Deployment for CashFlow AI..." -ForegroundColor Green

# Step 1: Create new project
Write-Host "📦 Creating new Railway project..." -ForegroundColor Blue
$projectBody = @{
    query = "mutation { projectCreate(input: {name: `"CashFlow AI`"}) { id name } }"
} | ConvertTo-Json

$project = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $projectBody
$projectId = $project.data.projectCreate.id
Write-Host "✅ Project created: $($project.data.projectCreate.name) (ID: $projectId)" -ForegroundColor Green

# Step 2: Add backend service
Write-Host "🔧 Adding backend service..." -ForegroundColor Blue
$backendBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"backend`", source: {repo: `"YOUR_GITHUB_USERNAME/code-project`", branch: `"master`", startCommand: `"gunicorn app.main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`", root: `"backend`", builder: `"DOCKERFILE`"}}) { id name } }"
} | ConvertTo-Json

$backend = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $backendBody
$backendId = $backend.data.serviceCreate.id
Write-Host "✅ Backend service created: $($backend.data.serviceCreate.name)" -ForegroundColor Green

# Step 3: Add frontend service  
Write-Host "🎨 Adding frontend service..." -ForegroundColor Blue
$frontendBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"frontend`", source: {repo: `"YOUR_GITHUB_USERNAME/code-project`", branch: `"master`", startCommand: `"npx serve -s . -l 3000`", root: `"frontend`", builder: `"NIXPACKS`"}}) { id name } }"
} | ConvertTo-Json

$frontend = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $frontendBody
$frontendId = $frontend.data.serviceCreate.id
Write-Host "✅ Frontend service created: $($frontend.data.serviceCreate.name)" -ForegroundColor Green

# Step 4: Add MongoDB
Write-Host "🗄️ Adding MongoDB..." -ForegroundColor Blue
$mongoBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"mongodb`", source: {image: `"mongo:latest`"}, variables: [{key: `"MONGO_URL`", value: `"${{MONGO_URL}}`"}]}) { id name } }"
} | ConvertTo-Json

$mongo = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $mongoBody
$mongoId = $mongo.data.serviceCreate.id
Write-Host "✅ MongoDB created: $($mongo.data.serviceCreate.name)" -ForegroundColor Green

# Step 5: Add Redis
Write-Host "🔴 Adding Redis..." -ForegroundColor Blue
$redisBody = @{
    query = "mutation { serviceCreate(projectId: `"$projectId`", input: {name: `"redis`", source: {image: `"redis:latest`"}, variables: [{key: `"REDIS_URL`", value: `"${{REDIS_URL}}`"}]}) { id name } }"
} | ConvertTo-Json

$redis = Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $redisBody
$redisId = $redis.data.serviceCreate.id
Write-Host "✅ Redis created: $($redis.data.serviceCreate.name)" -ForegroundColor Green

# Step 6: Set environment variables
Write-Host "⚙️ Setting environment variables..." -ForegroundColor Blue
$envBody = @{
    query = "mutation { environmentVariableUpsert(serviceId: `"$backendId`", input: [{key: `"GEMINI_API_KEY`", value: `"YOUR_GEMINI_API_KEY_HERE`"}, {key: `"SECRET_KEY`", value: `"$(openssl rand -hex 32)"`}]) { key value } }"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $envBody
Write-Host "✅ Environment variables set" -ForegroundColor Green

# Step 7: Deploy all services
Write-Host "🚀 Deploying services..." -ForegroundColor Blue
$deployBody = @{
    query = "mutation { serviceDeploy(serviceId: `"$backendId`") { id } }"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $deployBody

$deployFrontendBody = @{
    query = "mutation { serviceDeploy(serviceId: `"$frontendId`") { id } }"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://backboard.railway.app/graphql/v2" -Method POST -Headers $headers -Body $deployFrontendBody

Write-Host "✅ Deployment started!" -ForegroundColor Green
Write-Host "🌐 Your app will be available at: https://cashflow-ai.up.railway.app" -ForegroundColor Cyan
Write-Host "🔧 Check Railway dashboard for deployment status" -ForegroundColor Yellow

Write-Host "🎉 Railway deployment complete!" -ForegroundColor Green
