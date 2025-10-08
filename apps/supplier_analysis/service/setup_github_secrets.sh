#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Read .env file and set secrets/variables
while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi
    
    # Split the line into key and value
    key=$(echo "$line" | cut -d '=' -f 1)
    value=$(echo "$line" | cut -d '=' -f 2-)
    
    # Remove any quotes from the value
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    
    # Skip if key or value is empty
    if [[ -z "$key" || -z "$value" ]]; then
        continue
    fi
    
    # Set as GitHub secret
    echo "Setting secret: $key"
    gh secret set "$key" -b "$value"
    
    # Also set as variable
    echo "Setting variable: $key"
    gh variable set "$key" -b "$value"
done < .env

echo "All secrets and variables have been set successfully!"