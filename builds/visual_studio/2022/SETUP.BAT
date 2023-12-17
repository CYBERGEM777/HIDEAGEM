@echo off
SETLOCAL

:: Get the full path of the current directory
SET "script_dir=%~dp0"

:: Set the path to where your zlib dependency is located
SET "miniz_dependency_path=%script_dir%..\..\..\dependencies\miniz"
SET "libsodium_dependency_path=%script_dir%..\..\..\dependencies\libsodium"
SET "utf8proc_dependency_path=%script_dir%..\..\..\dependencies\utf8proc"

:: Set the path where you want to generate the Visual Studio project files for utf8proc
SET "utf8proc_build_dir=%script_dir%temp\utf8proc_vstudio"
SET "miniz_build_dir=%script_dir%temp\miniz_vstudio"

echo.
:: Reset the zlib repository
echo Resetting the miniz repository...
PUSHD "%miniz_dependency_path%"
git reset --hard
POPD
echo.


echo Generating Visual Studio project files for miniz...
echo.

:: Navigate to the utf8proc dependency directory
PUSHD "%miniz_dependency_path%"
git reset --hard
git clean -f

:: Run CMake to generate the project files
cmake -B "%miniz_dependency_path%" -G "Visual Studio 17 2022" -A x64
cmake --build "%miniz_dependency_path%" --config Release

:: Navigate back to the original directory
POPD

echo.

echo.
:: Reset the libsodium repository
echo Resetting the libsodium repository...
PUSHD "%libsodium_dependency_path%"
git reset --hard
POPD
echo.

echo.
:: Reset the utf8proc repository
echo Resetting the utf8proc repository...
PUSHD "%utf8proc_dependency_path%"
git reset --hard
POPD
echo.

:: Check if the build directory for utf8proc already exists
IF EXIST "%utf8proc_build_dir%" (
    echo Build directory for utf8proc already exists. Skipping project generation.
) ELSE (
    echo Generating Visual Studio project files for utf8proc...
    echo.

    :: Navigate to the utf8proc dependency directory
    PUSHD "%utf8proc_dependency_path%"

    :: Run CMake to generate the project files
    cmake -B "%utf8proc_build_dir%" -G "Visual Studio 17 2022" -A x64

    :: Navigate back to the original directory
    POPD
)
echo.

:: End of the script
ENDLOCAL
echo Setup complete.
echo.

pause
