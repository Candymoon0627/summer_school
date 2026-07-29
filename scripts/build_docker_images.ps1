$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$context = Join-Path $root (".tmp\docker_build_context_" + [guid]::NewGuid().ToString("N"))

New-Item -ItemType Directory -Force -Path $context | Out-Null

Copy-Item -LiteralPath (Join-Path $root "Dockerfile") -Destination $context
Copy-Item -LiteralPath (Join-Path $root "pyproject.toml") -Destination $context
Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination $context
Copy-Item -LiteralPath (Join-Path $root "alembic.ini") -Destination $context
Copy-Item -LiteralPath (Join-Path $root "app") -Destination $context -Recurse
Copy-Item -LiteralPath (Join-Path $root "scripts") -Destination $context -Recurse
if (Test-Path -LiteralPath (Join-Path $root "data")) {
    Copy-Item -LiteralPath (Join-Path $root "data") -Destination $context -Recurse
}

Set-Content -LiteralPath (Join-Path $context ".dockerignore") -Encoding ASCII -Value @"
__pycache__
*.py[cod]
*.egg-info
"@

$env:DOCKER_BUILDKIT = "0"
docker build -t edu_ai-api -t edu_ai-worker $context

Write-Host "Built Docker images from clean context: $context"
