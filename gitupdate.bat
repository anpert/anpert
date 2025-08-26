@echo off
setlocal enabledelayedexpansion

rem gitupdate.bat
rem %1 : suunta=START tai suunta=END  (oletus END)
rem %2 : paussi=TRUE tai paussi=FALSE (oletus TRUE)

rem Exit-koodit:
rem 1 = ei git-repo
rem 2 = virheelliset parametrit
rem 4 = kesken merge/rebase TAI pull/switch-virhe
rem 5 = add/diff/commit-virhe
rem 6 = push-virhe

:: ========== 0) Oletukset ja parametrit ==========
set "SUUNTA=END"
if not "%~1"=="" (
  if /i "%~1"=="START" ( set "SUUNTA=START" ) else if /i "%~1"=="END" ( set "SUUNTA=END" ) else (
    call :die "Suuntaparametri virheellinen (anna START tai END)." 2
  )
)

set "PAUSSI=TRUE"
if not "%~2"=="" (
  if /i "%~2"=="FALSE" ( set "PAUSSI=FALSE" ) else if /i "%~2"=="TRUE" ( set "PAUSSI=TRUE" ) else (
    rem tuntematon -> jätetään oletus TRUE
    set "PAUSSI=TRUE"
  )
)

:: ========== 1) Varmista että ollaan Git-repossa ==========
git rev-parse --is-inside-work-tree >nul 2>&1 || call :die "Virhe: Tätä skriptiä pitää ajaa Git-repositorion sisällä." 1

:: Hae repon nimi commit-viestiä varten
for /f "delims=" %%R in ('git rev-parse --show-toplevel 2^>nul') do for %%I in ("%%~fR") do set "REPO_NIMI=%%~nI"
if not defined REPO_NIMI set "REPO_NIMI=repo"

:: ========== 2) Aikaleima ==========
set "DATETIME="
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set DATETIME=%%I
if not defined DATETIME for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddHHmmss" 2^>nul') do set "DATETIME=%%I"

set "TIMESTAMP=!DATETIME:~0,4!-!DATETIME:~4,2!-!DATETIME:~6,2! !DATETIME:~8,2!:!DATETIME:~10,2!:!DATETIME:~12,2!"

:: ========== 3) Vahti: kesken oleva MERGE tai REBASE? ==========
git rev-parse -q --verify MERGE_HEAD >nul 2>&1 && call :die "Virhe: Keskeneräinen MERGE. Tee 'git merge --continue' tai 'git merge --abort'." 4
for /f "delims=" %%G in ('git rev-parse --git-path rebase-merge 2^>nul') do set "RBM=%%G"
for /f "delims=" %%G in ('git rev-parse --git-path rebase-apply 2^>nul') do set "RBA=%%G"
if exist "!RBM!" call :die "Virhe: Keskeneräinen REBASE (merge). Tee 'git rebase --continue' tai 'git rebase --abort'." 4
if exist "!RBA!" call :die "Virhe: Keskeneräinen REBASE (apply). Tee 'git rebase --continue' tai 'git rebase --abort'." 4

:: ========== 4) Git-toiminnot ==========
set "BRANCH=main"  rem vaihda tähän jos käytät muuta oletushaaraa

echo --------
echo SUUNTA: %SUUNTA%  BRANCH: %BRANCH%  REPO: %REPO_NIMI%
echo --------

rem Yritä switch, fallback checkoutiin
git switch "%BRANCH%" >nul 2>&1 || (
  git checkout "%BRANCH%" >nul 2>&1 || call :die "Virhe: Branchiin '%BRANCH%' vaihtaminen epäonnistui." 4
)

if /i "%SUUNTA%"=="END" (
  echo [END] Vedetään uusimmat (rebase)
  git pull --rebase origin "%BRANCH%" || call :die "Virhe: git pull --rebase epäonnistui." 4

  echo [END] Lisätään muutokset
  git add . || call :die "Virhe: git add epäonnistui." 5

  rem Onko stagingissa jotain? 0 = ei muutoksia, 1 = muutoksia, muu = virhe
  git diff --cached --quiet
  set "RC=!ERRORLEVEL!"
  if "%RC%"=="0" (
    echo [END] Ei muutoksia staged. Ohitetaan commit ja push.
  ) else (
    if "%RC%"=="1" (
      echo [END] Commit
      git commit -m "Automaattinen paivitys: %TIMESTAMP%" || call :die "Virhe: git commit epäonnistui." 5
      echo [END] Push
      git push origin "%BRANCH%" || call :die "Virhe: git push epäonnistui." 6
    ) else (
      call :die "Virhe: git diff --cached --quiet palautti odottamattoman koodin %RC%." 5
    )
  )
) else (
  echo [START] Vedetään uusimmat (rebase)
  git pull --rebase origin "%BRANCH%" || call :die "Virhe: git pull --rebase epäonnistui." 4
)

echo Valmis.
if /i "%PAUSSI%"=="TRUE" pause
exit /b 0

:: ===== apufunktio virheilmoituksille =====
:die
echo %~1
if /i "%PAUSSI%"=="TRUE" pause
exit /b %~2
