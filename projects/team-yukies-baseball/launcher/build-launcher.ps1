$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $PSScriptRoot "CardPreviewLauncher.cs"
$iconPath = Join-Path $projectRoot "card-template-html\assets\app-icon.ico"
$outputPath = Join-Path $projectRoot "TEAM-YUKIES-Card-Preview.exe"

foreach ($path in @($sourcePath, $iconPath)) {
    if (-not (Test-Path -LiteralPath $path)) {
        throw "Required file not found: $path"
    }
}

if (Test-Path -LiteralPath $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$compilerOptions = '/win32icon:"{0}" /optimize+' -f $iconPath

Add-Type `
    -TypeDefinition $source `
    -Language CSharp `
    -OutputAssembly $outputPath `
    -OutputType WindowsApplication `
    -CompilerOptions $compilerOptions

if (-not (Test-Path -LiteralPath $outputPath)) {
    throw "Launcher build did not create $outputPath"
}

Write-Host "Built: $outputPath"
