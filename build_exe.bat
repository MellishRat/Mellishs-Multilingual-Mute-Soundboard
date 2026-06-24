@echo off
title Build Soundboard EXE

echo Installing requirements...
py -m pip install -r requirements.txt

echo Installing PyInstaller...
py -m pip install pyinstaller

echo.
echo Building EXE...
py -m PyInstaller ^
    --onefile ^
    --windowed ^
    --clean ^
    --name "Mellishs_Multilingual_Mute_Soundboard" ^
    Mellishs_Multilingual_Mute_Soundboard_v1_2.py

echo.
echo Build complete.
echo EXE location:
echo dist\Mellishs_Multilingual_Mute_Soundboard.exe
echo.

pause