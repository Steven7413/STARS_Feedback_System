$TargetFile = "c:\Users\gonzo\.gemini\antigravity\scratch\stars-matrix\run_stars_matrix.bat"
$ShortcutFile = "$env:USERPROFILE\Desktop\STARS MATRIX.lnk"
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
$Shortcut.TargetPath = $TargetFile
$Shortcut.WorkingDirectory = "c:\Users\gonzo\.gemini\antigravity\scratch\stars-matrix"
$Shortcut.Description = "Launch STARS MATRIX System"
$Shortcut.IconLocation = "shell32.dll,290" 
$Shortcut.Save()
Write-Host "Shortcut created at $ShortcutFile"
