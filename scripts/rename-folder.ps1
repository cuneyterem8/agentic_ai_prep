# Cursor'u kapat, sonra bu scripti calistir:
#   cd C:\Users\cnytC\Desktop\code_projects
#   .\agenticai_ing_prep\scripts\rename-folder.ps1

$ErrorActionPreference = "Stop"
$parent = "C:\Users\cnytC\Desktop\code_projects"
$oldName = "agenticai_ing_prep"
$newName = "agentic_ai_prep"
$oldPath = Join-Path $parent $oldName
$newPath = Join-Path $parent $newName

if (-not (Test-Path $oldPath)) {
    if (Test-Path $newPath) {
        Write-Host "Klasor zaten yeniden adlandirilmis: $newPath"
        exit 0
    }
    throw "Kaynak klasor bulunamadi: $oldPath"
}

if (Test-Path $newPath) {
    throw "Hedef klasor zaten var: $newPath"
}

Rename-Item -Path $oldPath -NewName $newName
Write-Host "Tamam: $newPath"
Write-Host "Cursor'da File > Open Folder ile yeni klasoru ac."
