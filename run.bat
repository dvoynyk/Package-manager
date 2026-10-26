@echo off
if "%1"=="test" (
    python -m unittest discover -s tests -t .
) else (
    python src\main.py %*
)