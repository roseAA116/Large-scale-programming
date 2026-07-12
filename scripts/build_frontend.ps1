Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
  npm run build
} finally {
  Pop-Location
}
