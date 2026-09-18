Get-CimInstance Win32_Process | ForEach-Object {
    if ($_.CommandLine -match 'worker|uvicorn') {
        [PSCustomObject]@{
            ProcessId = $_.ProcessId
            CommandLine = $_.CommandLine
        }
    }
}
