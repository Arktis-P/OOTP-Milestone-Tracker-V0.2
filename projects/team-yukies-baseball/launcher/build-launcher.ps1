$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $PSScriptRoot "CardPreviewLauncher.cs"
$iconPath = Join-Path $projectRoot "card-template-html\assets\app-icon.ico"
$outputPath = Join-Path $projectRoot "Team Yukies Card Preview.exe"

foreach ($path in @($sourcePath, $iconPath)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required file not found: $path"
    }
}

if (Test-Path -LiteralPath $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

$csc = Get-Command csc.exe -ErrorAction SilentlyContinue
if ($csc) {
    $cscPath = $csc.Source
} else {
    $frameworkCandidates = @(
        "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
        "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe"
    )
    $cscPath = $frameworkCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

if (-not $cscPath) {
    throw "C# compiler (csc.exe) was not found."
}

& $cscPath /nologo /target:winexe /optimize+ "/win32icon:$iconPath" "/out:$outputPath" $sourcePath
if ($LASTEXITCODE -ne 0) {
    throw "csc.exe failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $outputPath)) {
    throw "Launcher build did not create $outputPath"
}

Write-Host "Built: $outputPath"
