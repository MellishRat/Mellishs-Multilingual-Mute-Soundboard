@echo off
title Build Mellish's Multilingual Mute Soundboard EXE
cd /d "%~dp0"

echo.
echo ============================================
echo  Mellish's Multilingual Mute Soundboard
echo  EXE Builder
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Please install Python 3.10+ and tick "Add Python to PATH".
    pause
    exit /b 1
)

echo Creating local build environment...
python -m venv .venv
if errorlevel 1 (
    echo Failed to create Python virtual environment.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Updating pip...
python -m pip install --upgrade pip

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building main soundboard EXE...
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "Mellishs_Multilingual_Mute_Soundboard" ^
  "Mellishs_Multilingual_Mute_Soundboard.py"

if errorlevel 1 (
    echo Main EXE build failed.
    pause
    exit /b 1
)

echo.
echo Building JSON editor EXE...
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "Phrase_Board_JSON_Editor" ^
  "Phrase_Board_JSON_Editor.py"

if errorlevel 1 (
    echo Editor EXE build failed.
    pause
    exit /b 1
)

echo.
echo Copying JSON files into dist folder...
copy /Y "host.json" "dist\host.json" >nul
copy /Y "board_2.json" "dist\board_2.json" >nul
copy /Y "board_3.json" "dist\board_3.json" >nul
copy /Y "board_4.json" "dist\board_4.json" >nul
copy /Y "board_5.json" "dist\board_5.json" >nul
copy /Y "board_settings.json" "dist\board_settings.json" >nul

echo.
echo Done.
echo Your EXEs and JSON files are in the dist folder.
echo.
pause
