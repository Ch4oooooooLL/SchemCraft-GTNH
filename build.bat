@echo off
echo Building SchemaCrafter GUI...

if exist SchemCraft.ico (
    python -m PyInstaller --noconfirm --onefile --windowed --name SchemaCrafter --icon SchemCraft.ico --add-data="SchemCraft.png;." main.py
) else (
    echo Note: SchemCraft.ico not found, building without exe icon
    python -m PyInstaller --noconfirm --onefile --windowed --name SchemaCrafter --add-data="SchemCraft.png;." main.py
)

echo Build complete!
echo Output: dist\SchemaCrafter.exe
pause
