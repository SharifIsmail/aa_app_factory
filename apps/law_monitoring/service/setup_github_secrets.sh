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
    
    # Set as GitHub secret. Ask user to confirm before setting.
    echo "Setting secret: $key"
    read -p "Are you sure you want to set this secret? (y/n): " confirm
    if [[ "$confirm" == "y" ]]; then
        gh secret set "$key" -b "$value"
    else
        echo "Skipping secret: $key"
    fi
    
    # Also set as variable. Ask user to confirm before setting.
    echo "Setting variable: $key"
    read -p "Are you sure you want to set this variable? (y/n): " confirm
    if [[ "$confirm" == "y" ]]; then
        gh variable set "$key" -b "$value"
    else
        echo "Skipping variable: $key"
    fi
done < .env

echo "All secrets and variables have been set successfully!"