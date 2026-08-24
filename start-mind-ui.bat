@echo off
setlocal
title MiND - Interface local
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo.
  echo O Python nao foi encontrado neste computador.
  echo Instale o Python 3.9 ou superior e marque a opcao para adiciona-lo ao PATH.
  echo.
  pause
  exit /b 1
)

if not exist ".venv-ui\Scripts\python.exe" (
  echo Preparando o MiND pela primeira vez...
  py -3 -m venv ".venv-ui"
  if errorlevel 1 goto :failure
)

echo Verificando componentes da interface...
".venv-ui\Scripts\python.exe" -m pip install --disable-pip-version-check -q -e ".[ui]"
if errorlevel 1 goto :failure

echo Abrindo o MiND no navegador. Para encerrar, feche esta janela.
".venv-ui\Scripts\mind.exe" ui
exit /b %errorlevel%

:failure
echo.
echo Nao foi possivel preparar o MiND. Copie a mensagem acima para o diagnostico.
echo.
pause
exit /b 1
