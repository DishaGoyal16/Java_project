$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force build/classes | Out-Null
    $sources = @(Get-ChildItem src -Filter *.java -Recurse | ForEach-Object { $_.FullName })
    & javac --release 17 -d build/classes @sources
    if ($LASTEXITCODE -ne 0) { throw "Java compilation failed" }
    & jar --create --file build/scms-rules.jar --main-class edu.tiet.scms.RulesServer -C build/classes .
    if ($LASTEXITCODE -ne 0) { throw "JAR packaging failed" }
} finally { Pop-Location }
