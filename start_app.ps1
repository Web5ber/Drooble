# Get the ngrok URL from ngrok's API
Write-Host "Getting ngrok URL..."
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels"
    $publicUrl = $response.tunnels[0].public_url
    Write-Host "Ngrok URL: $publicUrl"
    
    # Set the environment variable
    $env:WEBHOOK_URL = $publicUrl
    Write-Host "WEBHOOK_URL set to: $env:WEBHOOK_URL"
    
    # Start the FastAPI app
    Write-Host "Starting FastAPI app..."
    .\.venv\Scripts\python.exe app.py
}
catch {
    Write-Host "Error getting ngrok URL: $_"
    Write-Host "Make sure ngrok is running (use start_ngrok.ps1) and accessible at http://127.0.0.1:4040"
}
