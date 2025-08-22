@ECHO OFF

REM Minimal Sphinx make.bat
set SPHINXBUILD=sphinx-build
set SPHINXOPTS=
set SOURCEDIR=source
set BUILDDIR=_build

if "%1"=="" goto help

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
echo Common targets: html, clean

:end
exit /b

