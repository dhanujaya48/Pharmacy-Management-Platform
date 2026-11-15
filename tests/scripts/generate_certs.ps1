# PowerShell script to generate self-signed TLS certificates for Nginx
$ErrorActionPreference = "Stop"

$certDir = Join-Path $PSScriptRoot "..\docker\certs"
if (-not (Test-Path $certDir)) {
    New-Item -ItemType Directory -Path $certDir -Force | Out-Null
}

$crtPath = Join-Path $certDir "server.crt"
$keyPath = Join-Path $certDir "server.key"

if ((Test-Path $crtPath) -and (Test-Path $keyPath)) {
    Write-Host "TLS certificates already exist in $certDir. Skipping."
    exit 0
}

Write-Host "Generating self-signed SSL/TLS certificates via OpenSSL..."
if (Get-Command openssl -ErrorAction SilentlyContinue) {
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
        -keyout $keyPath `
        -out $crtPath `
        -subj "/C=IN/ST=Karnataka/L=Bengaluru/O=AlgionsAILabs/OU=DevOps/CN=localhost"
    Write-Host "Certificates generated successfully using OpenSSL."
} else {
    Write-Warning "OpenSSL command line not found. Creating placeholder cert files for build container testing."
    # Create empty placeholders so docker-compose volume mount doesn't fail
    New-Item -ItemType File -Path $crtPath -Force | Out-Null
    New-Item -ItemType File -Path $keyPath -Force | Out-Null
}
