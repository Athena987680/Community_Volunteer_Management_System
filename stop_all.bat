@echo off
setlocal

set "PORTS=8000,5173"

echo [INFO] Stopping services on ports %PORTS% ...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports = @(8000,5173);" ^
  "$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort } | Select-Object LocalPort, OwningProcess -Unique;" ^
  "if (-not $listeners) { Write-Host '[INFO] No listeners found on 8000/5173.'; exit 0 }" ^
  "$groups = $listeners | Group-Object OwningProcess;" ^
  "foreach ($group in $groups) {" ^
  "  $procId = [int]$group.Name;" ^
  "  $proc = Get-CimInstance Win32_Process -Filter (\"ProcessId=\" + $procId) -ErrorAction SilentlyContinue;" ^
  "  $portText = ($group.Group | Select-Object -ExpandProperty LocalPort | Sort-Object -Unique) -join ',';" ^
  "  if ($proc) { Write-Host (\"[INFO] Stopping PID {0} ({1}) ports={2}\" -f $procId, $proc.Name, $portText) } else { Write-Host (\"[INFO] Stopping PID {0} ports={1}\" -f $procId, $portText) };" ^
  "  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue;" ^
  "}" ^
  "Start-Sleep -Milliseconds 300;" ^
  "$left = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $ports -contains $_.LocalPort };" ^
  "if ($left) { Write-Host '[WARN] Some listeners still exist. Run this script again or stop them manually.'; exit 1 } else { Write-Host '[DONE] Ports 8000/5173 are released.' }"

if errorlevel 1 (
  echo [WARN] Stop script finished with warning.
) else (
  echo [DONE] Services stopped.
)

pause
