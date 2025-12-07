# Elevate to admin if not already
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Start-Process powershell -Verb runAs -ArgumentList "-File `"$PSCommandPath`""
    exit
}

# Kill all pythonw.exe processes
Get-Process pythonw -ErrorAction SilentlyContinue | Stop-Process -Force

# Navigate to folder
Set-Location "C:/close_page"

# Run Python script
python update.py

# Optional: pause to see output
Read-Host "Press Enter to exit"
