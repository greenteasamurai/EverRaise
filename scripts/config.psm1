# EverRaise Configuration Module
# This module provides shared configuration settings for EverRaise scripts

# Default ports for the application
$Script:DefaultBackendPort = 8000
$Script:DefaultFrontendPort = 5173

# Function to get backend port (can be overridden by an environment variable)
function Get-BackendPort {
    param (
        [Parameter(Mandatory=$false)]
        [int]$DefaultPort = $Script:DefaultBackendPort
    )
    
    # Check environment variable first
    $envPort = $env:EVERRAISE_BACKEND_PORT
    if ($envPort -and $envPort -match '^\d+$') {
        return [int]$envPort
    }
    
    # Return the default port if no environment variable is set
    return $DefaultPort
}

# Function to get frontend port (can be overridden by an environment variable)
function Get-FrontendPort {
    param (
        [Parameter(Mandatory=$false)]
        [int]$DefaultPort = $Script:DefaultFrontendPort
    )
    
    # Check environment variable first
    $envPort = $env:EVERRAISE_FRONTEND_PORT
    if ($envPort -and $envPort -match '^\d+$') {
        return [int]$envPort
    }
    
    # Return the default port if no environment variable is set
    return $DefaultPort
}

# Get API URL based on port
function Get-ApiUrl {
    param (
        [Parameter(Mandatory=$false)]
        [int]$Port = (Get-BackendPort)
    )
    
    return "http://localhost:$Port"
}

# Export functions and variables
Export-ModuleMember -Function Get-BackendPort, Get-FrontendPort, Get-ApiUrl
Export-ModuleMember -Variable DefaultBackendPort, DefaultFrontendPort 