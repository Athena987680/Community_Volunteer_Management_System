$defaultRoute = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
  Sort-Object RouteMetric, InterfaceMetric |
  Select-Object -First 1

$ip = $null
if ($defaultRoute) {
  $ip = Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $defaultRoute.InterfaceIndex -ErrorAction SilentlyContinue |
    Where-Object {
      $_.IPAddress -notlike '127.*' -and
      $_.IPAddress -notlike '169.254*' -and
      $_.IPAddress -notlike '172.20.*'
    } |
    Select-Object -First 1 -ExpandProperty IPAddress
}

if (-not $ip) {
  $ip = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
      $_.IPAddress -notlike '127.*' -and
      $_.IPAddress -notlike '169.254*' -and
      $_.IPAddress -notlike '172.20.*' -and
      $_.InterfaceAlias -notmatch 'VMware|vEthernet|Hyper-V|Virtual|Loopback'
    } |
    Select-Object -First 1 -ExpandProperty IPAddress
}

if ($ip) {
  Write-Output $ip
}
