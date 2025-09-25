@ECHO OFF

REM Go to the project root then step back one.
cd /d %~dp0/../

REM Launch the with the example settings
python src/main.py example

REM Pause so that any output can be read.
REM This may be removed later.
PAUSE