# Script to clean Git repository of sensitive credentials
# Usage: .\scripts\fix-git-secrets.ps1

param(
    [switch]$SkipBackup = $false,
    [string]$BfgPath = ".\bfg.jar",
    [switch]$Help = $false,
    [switch]$ForceJava = $false,
    [switch]$UseOlderBfg = $false
)

$ErrorActionPreference = "Stop"

# Show help
if ($Help) {
    Write-Host "EverRaise Git Repository Cleanup Script" -ForegroundColor Cyan
    Write-Host "This script uses BFG Repo Cleaner to remove sensitive credentials from Git history." -ForegroundColor Cyan
    Write-Host "`nUsage: .\scripts\fix-git-secrets.ps1 [-SkipBackup] [-BfgPath path\to\bfg.jar] [-ForceJava] [-UseOlderBfg] [-Help]" -ForegroundColor Cyan
    Write-Host "`nOptions:" -ForegroundColor Cyan
    Write-Host "  -SkipBackup        Skip creating a backup of the repository" -ForegroundColor White
    Write-Host "  -BfgPath           Path to the BFG JAR file (default: .\bfg.jar)" -ForegroundColor White
    Write-Host "  -ForceJava         Skip Java detection and try to run anyway" -ForegroundColor White
    Write-Host "  -UseOlderBfg       Download BFG 1.13.0 for Java 8 compatibility" -ForegroundColor White
    Write-Host "  -Help              Show this help message" -ForegroundColor White
    Write-Host "`nNotes:" -ForegroundColor Yellow
    Write-Host "- Download BFG from: https://rtyley.github.io/bfg-repo-cleaner/" -ForegroundColor White
    Write-Host "- This script must be run from the root of the repository" -ForegroundColor White
    Write-Host "- This will rewrite Git history, so coordinate with your team before running" -ForegroundColor White
    Write-Host "- BFG 1.14.0+ requires Java 11 or newer" -ForegroundColor White
    Write-Host "- Use -UseOlderBfg flag for Java 8 compatibility" -ForegroundColor White
    exit 0
}

# Banner
Write-Host "===== EverRaise Git Repository Cleanup =====" -ForegroundColor Cyan
Write-Host "This script will clean sensitive data from Git history" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Check for bfg.jar using multiple possible locations
$bfgLocations = @(
    $BfgPath,                         # User provided or default
    ".\bfg.jar",                      # Root directory
    ".\tools\bfg.jar",                # Tools subdirectory
    "$PSScriptRoot\bfg.jar",          # Same directory as script
    "$PSScriptRoot\..\bfg.jar",       # Parent directory of script
    "$env:USERPROFILE\Downloads\bfg.jar" # Downloads directory
)

$bfgFound = $false
foreach ($location in $bfgLocations) {
    if (Test-Path $location) {
        $BfgPath = $location
        $bfgFound = $true
        Write-Host "Found BFG Repo Cleaner at: $BfgPath" -ForegroundColor Green
        break
    }
}

# We'll set this after checking Java version
$bfgDownloadUrl = "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"

# Check if Java is installed and get its version
if (-not $ForceJava) {
    Write-Host "`nChecking for Java installation..." -ForegroundColor Yellow
    $javaFound = $false
    $javaVersionMajor = 0
    $javaVersionDetected = "Unknown"
    
    # Method 1: Try direct java command
    try {
        $javaOutput = java -version 2>&1
        $javaVersionText = $javaOutput -join " "
        $javaFound = $true
        
        # Parse Java version from output
        if ($javaVersionText -match 'version "([0-9]+\.[0-9]+)') {
            $versionString = $matches[1]
            if ($versionString -match '^1\.') {
                # Java 8 or older uses 1.x format
                $javaVersionMajor = [int]($versionString.Split('.')[1])
            } else {
                # Java 9+ uses just the major version number
                $javaVersionMajor = [int]($versionString.Split('.')[0])
            }
            $javaVersionDetected = $versionString
        } elseif ($javaVersionText -match 'version "([0-9]+)') {
            # Format for newer Java versions
            $javaVersionMajor = [int]$matches[1]
            $javaVersionDetected = $matches[1]
        }
        
        Write-Host "Java detected: $javaVersionText (Version $javaVersionDetected, Major Version $javaVersionMajor)" -ForegroundColor Green
    } catch {
        Write-Host "Java command not found in PATH" -ForegroundColor Yellow
    }
    
    # Method 2: Check registry for JRE/JDK
    if (-not $javaFound) {
        $javaKeys = @(
            "HKLM:\SOFTWARE\JavaSoft\Java Runtime Environment",
            "HKLM:\SOFTWARE\JavaSoft\Java Development Kit",
            "HKLM:\SOFTWARE\JavaSoft\JDK"
        )
        
        foreach ($key in $javaKeys) {
            if (Test-Path $key) {
                try {
                    $currentVersion = (Get-ItemProperty -Path $key -Name "CurrentVersion").CurrentVersion
                    $javaHome = (Get-ItemProperty -Path "$key\$currentVersion" -Name "JavaHome").JavaHome
                    if ($javaHome -and (Test-Path "$javaHome\bin\java.exe")) {
                        $env:Path = "$javaHome\bin;" + $env:Path
                        $javaFound = $true
                        
                        # Parse version from registry
                        if ($currentVersion -match '^1\.') {
                            $javaVersionMajor = [int]($currentVersion.Split('.')[1])
                        } else {
                            $javaVersionMajor = [int]($currentVersion.Split('.')[0])
                        }
                        $javaVersionDetected = $currentVersion
                        
                        Write-Host "Found Java in registry: $javaHome (version $currentVersion, Major Version $javaVersionMajor)" -ForegroundColor Green
                        break
                    }
                } catch {
                    # Continue checking other registry keys
                }
            }
        }
    }
    
    if (-not $javaFound) {
        Write-Host "`n[ERROR] Java is required but not found" -ForegroundColor Red
        Write-Host "Please install Java from: https://www.java.com/download/" -ForegroundColor Yellow
        Write-Host "Or use -ForceJava to try to run anyway (if Java is installed but not detected)" -ForegroundColor Yellow
        
        $installJava = Read-Host "Would you like to open the Java download page? (y/n)"
        if ($installJava -eq "y") {
            Start-Process "https://www.java.com/download/"
        }
        
        $forceJava = Read-Host "Try to continue anyway? (y/n)"
        if ($forceJava -ne "y") {
            exit 1
        }
    } else {
        # Check Java version and warn if incompatible with BFG 1.14+
        if ($javaVersionMajor -lt 11 -and -not $UseOlderBfg) {
            Write-Host "`n[WARNING] BFG 1.14.0+ requires Java 11 or newer, but you have Java $javaVersionDetected" -ForegroundColor Yellow
            Write-Host "You have a few options:" -ForegroundColor Yellow
            Write-Host "1. Install Java 11+ from: https://adoptium.net/" -ForegroundColor White
            Write-Host "2. Use an older version of BFG compatible with Java 8" -ForegroundColor White
            
            $useOlderBfgOption = Read-Host "Do you want to download an older BFG version compatible with Java 8? (y/n)"
            if ($useOlderBfgOption -eq "y") {
                $UseOlderBfg = $true
            } else {
                $upgradeJava = Read-Host "Do you want to open the Java 11+ download page? (y/n)"
                if ($upgradeJava -eq "y") {
                    Start-Process "https://adoptium.net/"
                    Write-Host "Please run this script again after installing Java 11+" -ForegroundColor Yellow
                    exit 0
                } else {
                    $continueAnyway = Read-Host "Try to continue with incompatible versions anyway? (y/n)"
                    if ($continueAnyway -ne "y") {
                        exit 1
                    }
                }
            }
        }
    }
}

# Set appropriate BFG download URL based on Java version
if ($UseOlderBfg -or ($javaVersionMajor -gt 0 -and $javaVersionMajor -lt 11)) {
    $bfgDownloadUrl = "https://repo1.maven.org/maven2/com/madgag/bfg/1.13.0/bfg-1.13.0.jar"
    Write-Host "`nUsing BFG 1.13.0 for Java 8 compatibility" -ForegroundColor Cyan
} else {
    $bfgDownloadUrl = "https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"
    Write-Host "`nUsing BFG 1.14.0 (requires Java 11+)" -ForegroundColor Cyan
}

# If BFG not found or we need to use an older version compatible with Java 8
if ((-not $bfgFound) -or ($UseOlderBfg -and $bfgFound)) {
    if ($UseOlderBfg -and $bfgFound) {
        Write-Host "`nReplacing existing BFG with Java 8 compatible version..." -ForegroundColor Yellow
    } else {
        Write-Host "`n[ERROR] BFG Repo Cleaner not found in any expected location" -ForegroundColor Red
        Write-Host "Please download it from: https://rtyley.github.io/bfg-repo-cleaner/" -ForegroundColor Yellow
        Write-Host "And place it in the repository root or specify path with -BfgPath" -ForegroundColor Yellow
    }
    
    $downloadNow = Read-Host "Would you like to download BFG now? (y/n)"
    
    if ($downloadNow -eq "y") {
        $downloadPath = ".\bfg.jar"
        
        Write-Host "Downloading BFG from $bfgDownloadUrl..." -ForegroundColor Yellow
        try {
            Invoke-WebRequest -Uri $bfgDownloadUrl -OutFile $downloadPath
            if (Test-Path $downloadPath) {
                Write-Host "Successfully downloaded BFG to $downloadPath" -ForegroundColor Green
                $BfgPath = $downloadPath
                $bfgFound = $true
            }
        } catch {
            Write-Host "Failed to download BFG: $_" -ForegroundColor Red
        }
    }
    
    if (-not $bfgFound) {
        exit 1
    }
}

# Create backup
$repoName = Split-Path -Leaf (Get-Location)
$backupPath = "..\$repoName-backup"

if (-not $SkipBackup) {
    Write-Host "`nCreating backup of repository..." -ForegroundColor Yellow
    if (Test-Path $backupPath) {
        $dateString = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "..\$repoName-backup-$dateString"
    }
    
    try {
        Copy-Item -Path . -Destination $backupPath -Recurse -Force
        Write-Host "[SUCCESS] Repository backed up to: $backupPath" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to create backup: $_" -ForegroundColor Red
        $continue = Read-Host "Continue without backup? (y/n)"
        if ($continue -ne "y") {
            exit 1
        }
    }
}

# Create patterns file if it doesn't exist
$patternsFile = "credentials-patterns.txt"
if (-not (Test-Path $patternsFile)) {
    Write-Host "`nCreating credentials patterns file..." -ForegroundColor Yellow
    @"
regex:([0-9a-zA-Z_]{24})[0-9a-zA-Z_]{8}
regex:([0-9a-zA-Z_]{32})[0-9a-zA-Z_]{16}
regex:"client_id": "([0-9]+-[a-z0-9]+).apps.googleusercontent.com"
regex:"client_secret": "([A-Za-z0-9_-]+)"
regex:GOOGLE_CLIENT_ID=([0-9]+-[a-z0-9]+).apps.googleusercontent.com
regex:GOOGLE_CLIENT_SECRET=([A-Za-z0-9_-]+)
"@ | Out-File -FilePath $patternsFile -Encoding utf8
    Write-Host "[SUCCESS] Created $patternsFile" -ForegroundColor Green
}

# Run BFG to clean repository
Write-Host "`nCleaning repository with BFG..." -ForegroundColor Yellow
Write-Host "Removing sensitive files..." -ForegroundColor Yellow

# Verify the jar file is accessible
try {
    $jarFileInfo = Get-Item $BfgPath -ErrorAction Stop
    $jarFileSizeKB = [math]::Round($jarFileInfo.Length / 1KB, 2)
    Write-Host "BFG JAR file size: $jarFileSizeKB KB" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Cannot access BFG JAR file: $_" -ForegroundColor Red
    $recoverableBfg = $false
    
    # Try to recover by downloading again
    $downloadAgain = Read-Host "Try to download BFG again? (y/n)"
    if ($downloadAgain -eq "y") {
        Write-Host "Downloading BFG from $bfgDownloadUrl..." -ForegroundColor Yellow
        try {
            Invoke-WebRequest -Uri $bfgDownloadUrl -OutFile $BfgPath
            if (Test-Path $BfgPath) {
                Write-Host "Successfully downloaded BFG to $BfgPath" -ForegroundColor Green
                $recoverableBfg = $true
            }
        } catch {
            Write-Host "Failed to download BFG: $_" -ForegroundColor Red
        }
    }
    
    if (-not $recoverableBfg) {
        exit 1
    }
}

# Test Java compatibility with BFG before running main operations
Write-Host "`nTesting Java compatibility with BFG..." -ForegroundColor Yellow
$testCommand = Start-Process -FilePath "java" -ArgumentList "-jar", $BfgPath, "--version" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "NUL" -RedirectStandardError "$env:TEMP\bfg-test-error.txt"

if ($testCommand.ExitCode -ne 0) {
    $errorOutput = Get-Content "$env:TEMP\bfg-test-error.txt" -ErrorAction SilentlyContinue
    if ($errorOutput -match "UnsupportedClassVersionError") {
        Write-Host "`n[ERROR] Java version compatibility issue detected!" -ForegroundColor Red
        Write-Host "The BFG version you're using requires a newer Java version than installed." -ForegroundColor Red
        Write-Host "Error details: $errorOutput" -ForegroundColor Yellow
        
        $tryOlderBfg = Read-Host "Would you like to try downloading an older BFG version compatible with Java 8? (y/n)"
        if ($tryOlderBfg -eq "y") {
            $bfgDownloadUrl = "https://repo1.maven.org/maven2/com/madgag/bfg/1.13.0/bfg-1.13.0.jar"
            Write-Host "Downloading Java 8 compatible BFG from $bfgDownloadUrl..." -ForegroundColor Yellow
            try {
                Invoke-WebRequest -Uri $bfgDownloadUrl -OutFile $BfgPath
                if (Test-Path $BfgPath) {
                    Write-Host "Successfully downloaded BFG to $BfgPath" -ForegroundColor Green
                    
                    # Test again with the older version
                    $testCommand = Start-Process -FilePath "java" -ArgumentList "-jar", $BfgPath, "--version" -NoNewWindow -Wait -PassThru -RedirectStandardOutput "NUL" -RedirectStandardError "$env:TEMP\bfg-test-error.txt"
                    if ($testCommand.ExitCode -ne 0) {
                        $errorOutput = Get-Content "$env:TEMP\bfg-test-error.txt" -ErrorAction SilentlyContinue
                        Write-Host "`n[ERROR] Still having compatibility issues with older BFG version:" -ForegroundColor Red
                        Write-Host "Error details: $errorOutput" -ForegroundColor Yellow
                        $continue = Read-Host "Try to continue anyway? (y/n)"
                        if ($continue -ne "y") {
                            exit 1
                        }
                    } else {
                        Write-Host "[SUCCESS] Older BFG version is compatible with your Java installation" -ForegroundColor Green
                    }
                }
            } catch {
                Write-Host "Failed to download older BFG version: $_" -ForegroundColor Red
                $continue = Read-Host "Try to continue anyway? (y/n)"
                if ($continue -ne "y") {
                    exit 1
                }
            }
        } else {
            $continue = Read-Host "Try to continue anyway? (y/n)"
            if ($continue -ne "y") {
                exit 1
            }
        }
    } else {
        Write-Host "`n[WARNING] BFG test command failed, but not due to Java version compatibility" -ForegroundColor Yellow
        Write-Host "Error details: $errorOutput" -ForegroundColor Yellow
        $continue = Read-Host "Try to continue anyway? (y/n)"
        if ($continue -ne "y") {
            exit 1
        }
    }
} else {
    Write-Host "[SUCCESS] BFG is compatible with your Java installation" -ForegroundColor Green
}

# List of sensitive files to remove
$sensitiveFiles = @(
    "token.json",
    "credentials.json",
    ".env"
)

$success = $true

foreach ($file in $sensitiveFiles) {
    Write-Host "Removing $file from history..." -ForegroundColor Yellow
    try {
        # Run java command with explicit error handling
        $process = Start-Process -FilePath "java" -ArgumentList "-jar", $BfgPath, "--delete-files", $file -NoNewWindow -Wait -PassThru
        if ($process.ExitCode -ne 0) {
            Write-Host "[WARNING] BFG reported non-zero exit code: $($process.ExitCode)" -ForegroundColor Yellow
            $success = $false
        }
    } catch {
        Write-Host "[ERROR] Failed to execute BFG for file $file : $_" -ForegroundColor Red
        $success = $false
    }
}

# Replace sensitive text patterns
Write-Host "Replacing sensitive text patterns..." -ForegroundColor Yellow
try {
    $process = Start-Process -FilePath "java" -ArgumentList "-jar", $BfgPath, "--replace-text", $patternsFile -NoNewWindow -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        Write-Host "[WARNING] BFG reported non-zero exit code: $($process.ExitCode)" -ForegroundColor Yellow
        $success = $false
    }
} catch {
    Write-Host "[ERROR] Failed to execute BFG for pattern replacement: $_" -ForegroundColor Red
    $success = $false
}

if (-not $success) {
    Write-Host "`n[WARNING] Some BFG operations reported issues." -ForegroundColor Yellow
    $continue = Read-Host "Continue with git cleanup anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Clean up refs and git garbage collection
Write-Host "`nCleaning up repository..." -ForegroundColor Yellow
Write-Host "This will expire reflog and perform aggressive garbage collection." -ForegroundColor Yellow
$confirm = Read-Host "Continue? (y/n)"

if ($confirm -eq "y") {
    Write-Host "Running git reflog expire..." -ForegroundColor Yellow
    & git reflog expire --expire=now --all
    
    Write-Host "Running git gc..." -ForegroundColor Yellow
    & git gc --prune=now --aggressive
    
    Write-Host "[SUCCESS] Repository cleanup complete!" -ForegroundColor Green
} else {
    Write-Host "Skipped repository cleanup" -ForegroundColor Yellow
}

# Final instructions
Write-Host "`n===== Next Steps =====" -ForegroundColor Cyan
Write-Host "1. Push the cleaned repository to remote:" -ForegroundColor White
Write-Host "   If your branch already has an upstream configured:" -ForegroundColor Yellow
Write-Host "     git push origin --force" -ForegroundColor Yellow
Write-Host "   If your branch doesn't have an upstream configured:" -ForegroundColor Yellow
Write-Host "     git push --set-upstream origin master --force" -ForegroundColor Yellow
Write-Host "2. Tell your team to clone a fresh copy of the repository" -ForegroundColor White
Write-Host "3. Create new OAuth credentials since old ones are compromised" -ForegroundColor White
Write-Host "4. Use .env.example as a template for creating a new .env file" -ForegroundColor White

# Check if the current branch has an upstream
$currentBranch = & git rev-parse --abbrev-ref HEAD
$hasUpstream = $false
$upstreamCheck = & git rev-parse --abbrev-ref "$currentBranch@{upstream}" 2>$null
if ($LASTEXITCODE -eq 0) {
    $hasUpstream = $true
}

# Display suggested command based on branch configuration
Write-Host "`nSuggested push command for your current branch '$currentBranch':" -ForegroundColor Cyan
if ($hasUpstream) {
    Write-Host "  git push origin --force" -ForegroundColor Green
} else {
    Write-Host "  git push --set-upstream origin $currentBranch --force" -ForegroundColor Green
}

Write-Host "======================" -ForegroundColor Cyan 