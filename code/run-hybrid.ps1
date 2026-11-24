param([switch]$Demo,[switch]$Diagnostics)
& "$PSScriptRoot/../scripts/Start-SCMS.ps1" -NoDashboard -Demo:$Demo -Diagnostics:$Diagnostics
