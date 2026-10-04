@echo off
chcp 65001 >nul
TITLE Установка плагина и мода на сервер Endstone

echo ========================================================
echo   Установка плагина и аддона "Скалковая Эпидемия"
echo ========================================================
echo.
set "SERVER_DIR=%~dp0..\endstone-0.11.12-windows-x86_64\bedrock_server"
set "MOD_DIR=%~dp0..\Мод"
set "PLUGINS_DIR=%~dp0"

if not exist "%SERVER_DIR%" (
    echo [ОШИБКА] Папка сервера не найдена по пути: %SERVER_DIR%
    pause
    exit /b 1
)

echo [1/3] Копирование Python-плагина (.whl) в папку plugins сервера...
if not exist "%SERVER_DIR%\plugins" mkdir "%SERVER_DIR%\plugins"
copy /Y "%PLUGINS_DIR%\endstone_sculk_epidemic-1.0.0-py3-none-any.whl" "%SERVER_DIR%\plugins\"

echo [2/3] Копирование Behavior Pack (мод)...
if not exist "%SERVER_DIR%\development_behavior_packs" mkdir "%SERVER_DIR%\development_behavior_packs"
xcopy /E /I /Y "%MOD_DIR%\sculk_epidemic_bp" "%SERVER_DIR%\development_behavior_packs\sculk_epidemic_bp"

echo [3/3] Копирование Resource Pack (ресурсы)...
if not exist "%SERVER_DIR%\development_resource_packs" mkdir "%SERVER_DIR%\development_resource_packs"
xcopy /E /I /Y "%MOD_DIR%\sculk_epidemic_rp" "%SERVER_DIR%\development_resource_packs\sculk_epidemic_rp"

echo.
echo ========================================================
echo   Установка успешно завершена!
echo   Теперь запустите сервер через start.cmd
echo ========================================================
pause
