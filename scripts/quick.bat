@echo off

isort src
if errorlevel 1 exit /b %errorlevel%

echo.
echo isort checks passed

black src
if errorlevel 1 exit /b %errorlevel%

echo.
echo black checks passed

flake8 src
if errorlevel 1 exit /b %errorlevel%

echo.
echo flake8 checks passed

mypy src
if errorlevel 1 exit /b %errorlevel%

echo.
echo mypy checks passed

echo.
echo ============ QUICK CHECKS PASSED ============
