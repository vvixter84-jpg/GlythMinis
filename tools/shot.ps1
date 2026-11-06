# Dev helper: capture the GlythMinis window without stealing focus or depending
# on z-order.  PrintWindow with PW_RENDERFULLCONTENT renders the Tk canvas even
# when the window is partly covered.
# Usage: powershell -File tools\shot.ps1 [-Out build\shot.png] [-Title "GlythMinis 1.1*"] [-Restore]
param(
    [string]$Out = "build\shot.png",
    [string]$Title = "GlythMinis 1.1*",
    [switch]$Restore
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Add-Type -AssemblyName System.Drawing

if (-not ("WinCap" -as [type])) {
    Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public static class WinCap {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int cmd);
}
"@
}

$proc = Get-Process | Where-Object { $_.MainWindowTitle -like $Title } | Select-Object -First 1
if (-not $proc -or $proc.MainWindowHandle -eq 0) {
    Write-Output "WINDOW_NOT_FOUND"
    exit 1
}
$hwnd = $proc.MainWindowHandle

if ($Restore) {
    # SW_SHOWNOACTIVATE: bring it back from the taskbar without stealing focus
    # from whatever is running fullscreen.
    [WinCap]::ShowWindow($hwnd, 4) | Out-Null
    Start-Sleep -Milliseconds 350
}

$rect = New-Object WinCap+RECT
[WinCap]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -lt 50 -or $height -lt 50) {
    Write-Output "BAD_RECT $width x $height"
    exit 1
}

$bmp = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $graphics.GetHdc()
$ok = [WinCap]::PrintWindow($hwnd, $hdc, 2)
$graphics.ReleaseHdc($hdc)
$graphics.Dispose()

$path = Join-Path $root $Out
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
$bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output ("SAVED {0} {1}x{2} printwindow={3}" -f $path, $width, $height, $ok)
