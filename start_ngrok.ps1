# Start ngrok in the background
Write-Host "Starting ngrok..."
$ngrokProcess = Start-Process -FilePath "ngrok" -ArgumentList "http", "8000" -PassThru -WindowStyle Hidden

# Wait for ngrok to start
Start-Sleep -Seconds 3

# Get the ngrok URL from ngrok's API
Write-Host "Getting ngrok URL..."
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels"
    $publicUrl = $response.tunnels[0].public_url
    Write-Host "Ngrok URL: $publicUrl"
    Write-Host "Ngrok is now running. Use start_app.ps1 to start your bot."
    Write-Host "Press Ctrl+C to stop ngrok."
    
    # Keep the script running to maintain ngrok
    Wait-Process -Id $ngrokProcess.Id
}
catch {
    Write-Host "Error getting ngrok URL: $_"
    Write-Host "Make sure ngrok is running and accessible at http://127.0.0.1:4040"
    if ($ngrokProcess -and !$ngrokProcess.HasExited) {
        Stop-Process -Id $ngrokProcess.Id -Force
    }
}
