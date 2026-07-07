@echo off

isort src tests
if errorlevel 1 exit /b %errorlevel%

echo.
echo isort checks passed

black src tests
if errorlevel 1 exit /b %errorlevel%

echo.
echo black checks passed

flake8 src tests
if errorlevel 1 exit /b %errorlevel%

echo.
echo flake8 checks passed

mypy src tests
if errorlevel 1 exit /b %errorlevel%

echo.
echo mypy checks passed

pytest tests ^
    --cov=src ^
    --cov-report=term-missing ^
    --cov-fail-under=100

if errorlevel 1 exit /b %errorlevel%

echo.
echo pytest checks complete

echo.
echo ============ ENFORCED CHECKS PASSED ============