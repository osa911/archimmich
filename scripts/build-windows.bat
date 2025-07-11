@echo off
echo Running build-windows.bat script...

:: Get version from version.txt
set /p VERSION=<version.txt

:: Run PyInstaller
pyinstaller ^
  --onedir ^
  --windowed ^
  --optimize "2" ^
  --icon="src/resources/favicon-180.png" ^
  --add-data "src/resources/*;src/resources" ^
  --collect-binaries "_internal" ^
  --distpath "dist" ^
  --paths="src" ^
  --name "ArchImmich" ^
  --collect-all "PyQt5" ^
  --collect-all "requests" ^
  src/main.py

:: Create release directory if it doesn't exist
if not exist "release" mkdir release

:: Create zip file
cd dist\ArchImmich
powershell Compress-Archive -Path * -DestinationPath ..\..\release\ArchImmich_Windows_v%VERSION%.zip -Force
cd ..\..

echo Windows build completed successfully!