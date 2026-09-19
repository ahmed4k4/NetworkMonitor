Get-Service | Where-Object { $_.Name -like "postgresql*" } | ForEach-Object {
    "SERVICE: $($_.Name) STATUS=$($_.Status)"
}