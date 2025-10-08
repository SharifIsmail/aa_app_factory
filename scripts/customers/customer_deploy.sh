#!/bin/bash
### Customer Deployment Script for Pharia Apps
### Run this script from anywhere as `./customer_deploy.sh`
###
### Required: Create a .env file in the same directory as this script with your configuration
### See .env.example for reference

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Check if .env file exists next to this script
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env file not found at $ENV_FILE"
    echo ""
    echo "Please create a .env file in the same directory as this script."
    echo "You can copy and modify the .env.example file."
    exit 1
fi

echo "Loading configuration from: $ENV_FILE"
source "$ENV_FILE"

# Validate required variables
echo "=== Configuration Check ==="
echo "PHARIAOS_MANAGER_URL: ${PHARIAOS_MANAGER_URL}"
echo "IMAGE_REGISTRY: ${IMAGE_REGISTRY}"
echo "IMAGE_TAG: ${IMAGE_TAG}"
echo "SERVICE_AUTHENTICATION_TOKEN: ${SERVICE_AUTHENTICATION_TOKEN:0:20}..."

# Check for required global variables
missing_vars=()
[[ -z "$PHARIAOS_MANAGER_URL" ]] && missing_vars+=("PHARIAOS_MANAGER_URL")
[[ -z "$IMAGE_REGISTRY" ]] && missing_vars+=("IMAGE_REGISTRY")
[[ -z "$IMAGE_TAG" ]] && missing_vars+=("IMAGE_TAG")
[[ -z "$SERVICE_AUTHENTICATION_TOKEN" ]] && missing_vars+=("SERVICE_AUTHENTICATION_TOKEN")
[[ -z "$SERVICE_PHARIA_KERNEL_URL" ]] && missing_vars+=("SERVICE_PHARIA_KERNEL_URL")
[[ -z "$SERVICE_PHARIA_AUTH_SERVICE_URL" ]] && missing_vars+=("SERVICE_PHARIA_AUTH_SERVICE_URL")
[[ -z "$SERVICE_PHARIA_IAM_ISSUER_URL" ]] && missing_vars+=("SERVICE_PHARIA_IAM_ISSUER_URL")
[[ -z "$SERVICE_PHARIA_DATA_URL" ]] && missing_vars+=("SERVICE_PHARIA_DATA_URL")
[[ -z "$SERVICE_INFERENCE_API_URL" ]] && missing_vars+=("SERVICE_INFERENCE_API_URL")
[[ -z "$SERVICE_COMPLETION_MODEL_NAME" ]] && missing_vars+=("SERVICE_COMPLETION_MODEL_NAME")

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo ""
    echo "ERROR: Missing required environment variables in $ENV_FILE:"
    printf ' - %s\n' "${missing_vars[@]}"
    echo ""
    echo "Please update your .env file with these variables."
    exit 1
fi

echo "✅ Configuration looks good!"
echo ""

# Base URL and authorization token
BASE_URL="${PHARIAOS_MANAGER_URL}/api/usecases"

# Ask for the usecase name
read -p "Enter the usecase name as it will appear in the UI: " usecase_name

# Ask for the usecase description
read -p "Enter the usecase description: " usecase_description

# Ask for the isPublic flag. Flag is false by default
read -p "Usecase should be public? (y/n): " isPublic
if [ "$isPublic" != "y" ]; then
  isPublic="false"
  # Ask for the project id to attach the usecase to
  read -p "Enter a PhariaStudio project id to attach the usecase to: " projectId
  # Verify that the project id is not empty
  if [ -z "$projectId" ]; then
    echo "ERROR: Project id is required"
    exit 1
  fi
else
  isPublic="true"
  projectId=""
fi

# Available apps (hardcoded for simplicity)
available_apps=("supplier_analysis" "law_monitoring" "agentic_app_template" "supplier_briefing")

# Display available apps with numbers
echo ""
echo "Available apps:"
for i in "${!available_apps[@]}"; do
    echo "$((i+1)). ${available_apps[i]}"
done

# Ask user to pick a number
echo ""
read -p "Select an app by number (1-${#available_apps[@]}): " app_choice

# Validate the choice
if ! [[ "$app_choice" =~ ^[0-9]+$ ]] || [ "$app_choice" -lt 1 ] || [ "$app_choice" -gt ${#available_apps[@]} ]; then
    echo "ERROR: Invalid choice. Please enter a number between 1 and ${#available_apps[@]}"
    exit 1
fi

# Get the selected app name
app_name="${available_apps[$((app_choice-1))]}"
echo "Selected app: $app_name"

# Check app-specific variables
if [ "$app_name" = "law_monitoring" ]; then
    echo ""
    echo "=== Checking law_monitoring specific variables ==="
    
    law_missing_vars=()
    [[ -z "$SERVICE_PHARIA_DATA_STAGE_NAME" ]] && law_missing_vars+=("SERVICE_PHARIA_DATA_STAGE_NAME")
    [[ -z "$SERVICE_STORAGE_TYPE" ]] && law_missing_vars+=("SERVICE_STORAGE_TYPE")
    [[ -z "$SERVICE_POSTGRES_SECRET_NAME" ]] && law_missing_vars+=("SERVICE_POSTGRES_SECRET_NAME")
    [[ -z "$SERVICE_POSTGRES_SECRET_KEY" ]] && law_missing_vars+=("SERVICE_POSTGRES_SECRET_KEY")
    
    if [ ${#law_missing_vars[@]} -gt 0 ]; then
        echo "ERROR: Missing law_monitoring specific variables in $ENV_FILE:"
        printf ' - %s\n' "${law_missing_vars[@]}"
        echo ""
        echo "Please add these to your .env file:"
        echo "SERVICE_PHARIA_DATA_STAGE_NAME=eu-law-stage0"
        echo "SERVICE_STORAGE_TYPE=pharia_data_synced_sqlite"
        echo "SERVICE_POSTGRES_SECRET_NAME=pharia-assistant-postgresql-secret"
        echo "SERVICE_POSTGRES_SECRET_KEY=STACKIT_POSTGRES_URL"
        exit 1
    fi
elif [ "$app_name" = "supplier_analysis" ] || [ "$app_name" = "agentic_app_template" ]; then
    echo ""
    echo "=== Checking API key variables ==="
    
    api_missing_vars=()
    [[ -z "$SERPER_API_KEY" ]] && api_missing_vars+=("SERPER_API_KEY")
    [[ -z "$ABSTRACT_API_KEY" ]] && api_missing_vars+=("ABSTRACT_API_KEY")
    
    if [ ${#api_missing_vars[@]} -gt 0 ]; then
        echo "ERROR: Missing API key variables for $app_name in $ENV_FILE:"
        printf ' - %s\n' "${api_missing_vars[@]}"
        echo ""
        echo "Please add these to your .env file:"
        echo "SERPER_API_KEY=your_serper_api_key"
        echo "ABSTRACT_API_KEY=your_abstract_api_key"
        exit 1
    fi
elif [ "$app_name" = "supplier_briefing" ]; then
    echo ""
    echo "=== Checking supplier_briefing specific variables ==="
    
    supplier_briefing_missing_vars=()
    [[ -z "$SERVICE_STUDIO_URL" ]] && supplier_briefing_missing_vars+=("SERVICE_STUDIO_URL")
    [[ -z "$SERVICE_STUDIO_PROJECT_NAME" ]] && supplier_briefing_missing_vars+=("SERVICE_STUDIO_PROJECT_NAME")
    
    if [ ${#supplier_briefing_missing_vars[@]} -gt 0 ]; then
        echo "ERROR: Missing supplier_briefing specific variables in $ENV_FILE:"
        printf ' - %s\n' "${supplier_briefing_missing_vars[@]}"
        echo ""
        echo "Please add these to your .env file:"
        echo "SERVICE_PHARIA_STUDIO_URL=https://pharia-studio.xxx.pharia.com"
        echo "SERVICE_PHARIA_STUDIO_PROJECT_NAME=supplier-briefing"
        exit 1
    fi
fi

echo ""
echo "=== Starting Deployment Process ==="

# Initial values for pagination
page=1
limit=100
has_more=true
all_results=()

# Loop until there are no more pages
while $has_more; do
  echo "Fetching existing usecases (page $page)..."
  # Make the API call for the current page
  response=$(curl --silent --request GET \
    --url "$BASE_URL?page=$page&limit=$limit" \
    --header "Authorization: Bearer ${SERVICE_AUTHENTICATION_TOKEN}")
  
  # Check if the response is valid JSON and contains the expected structure
  if ! echo "$response" | jq -e '.data' > /dev/null 2>&1; then
    echo "Error: Invalid response from API"
    echo "Response: $response"
    exit 1
  fi
  
  # Extract just the data array from this page
  page_data=$(echo "$response" | jq '.data')
  
  # Check if we got any results
  result_count=$(echo "$page_data" | jq '. | length')
  
  if [ "$result_count" -eq 0 ] || [ -z "$result_count" ]; then
    has_more=false
    echo "No more results."
  elif [ "$(echo "$response" | jq '.status')" -eq 400 ]; then
    echo "Error: detail: $(echo "$response" | jq -r '.detail')"
    exit 1
  else
    # Add this page's data to our collection
    all_results+=("$page_data")
    echo "Got $result_count results on page $page"
    page=$((page+1))
  fi
done

# Combine all results into a single JSON array
if [ ${#all_results[@]} -eq 0 ]; then
  echo "No existing usecases found"
  combined_results="[]"
else
  combined_results=$(jq -s 'add' <<< "${all_results[@]}")
  echo "Total existing usecases: $(echo "$combined_results" | jq '. | length')"
fi

# Create the usecase
echo ""
echo "Creating usecase: $usecase_name..."
response=$(curl --request POST \
  --url "${BASE_URL}" \
  --header "Authorization: Bearer ${SERVICE_AUTHENTICATION_TOKEN}" \
  --header "Content-Type: application/json" \
  --data "{
  \"description\": \"${usecase_description}\",
  \"name\": \"${usecase_name}\",
  \"projectId\": \"${projectId}\",
  \"isPublic\": ${isPublic}
}")

# If response is 409 - conflict, then the usecase already exists
if [ "$(echo "$response" | jq '.status')" -eq 409 ]; then
  echo "ℹ️  Usecase already exists, using existing one"
  # extract usecase id from all_usecases.json
  usecase_id=$(echo "$combined_results" | jq -r ".[] | select(.name == \"${usecase_name}\") | .id")
  echo "Usecase ID: ${usecase_id}"
elif [ "$(echo "$response" | jq '.status')" -eq 400 ]; then
  echo "Error: detail: $(echo "$response" | jq -r '.detail')"
  exit 1
else
  echo "✅ Usecase created successfully"
  usecase_id=$(echo "$response" | jq -r '.id')
  echo "Usecase ID: ${usecase_id}"
fi

# Set general env variables. Overrides baked-in vars for maximum flexibility across different clusters
env_json='"SERVICE_ENABLE_CORS":"false"'
env_json+=',"SERVICE_PHARIA_KERNEL_URL":"'"${SERVICE_PHARIA_KERNEL_URL}"'"'
env_json+=',"SERVICE_PHARIA_AUTH_SERVICE_URL":"'"${SERVICE_PHARIA_AUTH_SERVICE_URL}"'"'
env_json+=',"SERVICE_PHARIA_IAM_ISSUER_URL":"'"${SERVICE_PHARIA_IAM_ISSUER_URL}"'"'
env_json+=',"SERVICE_PHARIA_DATA_URL":"'"${SERVICE_PHARIA_DATA_URL}"'"'
env_json+=',"SERVICE_INFERENCE_API_URL":"'"${SERVICE_INFERENCE_API_URL}"'"'
env_json+=',"SERVICE_COMPLETION_MODEL_NAME":"'"${SERVICE_COMPLETION_MODEL_NAME}"'"'
env_json+=',"SERVICE_AUTHENTICATION_TOKEN":"'"${SERVICE_AUTHENTICATION_TOKEN}"'"'

# Set app specific env variables
if [ "$app_name" = "law_monitoring" ]; then
  env_json+=',"SERVICE_PHARIA_DATA_STAGE_NAME":"'"${SERVICE_PHARIA_DATA_STAGE_NAME}"'"'
  env_json+=',"SERVICE_STORAGE_TYPE":"'"${SERVICE_STORAGE_TYPE}"'"'
fi

# Set app-specific API keys (injectable for customer deployments)
if [ "$app_name" = "supplier_analysis" ] || [ "$app_name" = "agentic_app_template" ] || [ "$app_name" = "supplier_briefing" ]; then
  env_json+=',"SERPER_API_KEY":"'"${SERPER_API_KEY}"'"'
  env_json+=',"ABSTRACT_API_KEY":"'"${ABSTRACT_API_KEY}"'"'
fi

if [ "$app_name" = "supplier_briefing" ]; then
  env_json+=',"SERVICE_STUDIO_URL":"'"${SERVICE_STUDIO_URL}"'"'
  env_json+=',"SERVICE_STUDIO_PROJECT_NAME":"'"${SERVICE_STUDIO_PROJECT_NAME}"'"'
  env_json+=',"SERVICE_ENABLE_DATA_PREPARATION":"true"'
fi

echo "Environment variables configured for deployment"

# Set resources for apps that require specific resource limits
resources_json=""
if [ "$app_name" = "supplier_briefing" ]; then
  echo "Setting resource limits for supplier_briefing"
  
  resources_json=',"resources":{
    "limits":{
      "cpu":"2",
      "memory":"16Gi"
    },
    "requests":{
      "cpu":"2",
      "memory":"8Gi"
    }
  }'
fi

# Set secretEnvVars for apps that require database access
secret_env_vars_json=""
if [ "$app_name" = "law_monitoring" ]; then
  echo "Using database secret: ${SERVICE_POSTGRES_SECRET_NAME} with key: ${SERVICE_POSTGRES_SECRET_KEY}"
  
  secret_env_vars_json=',"secretEnvVars":[
    {
      "name":"SERVICE_DATABASE_URL",
      "secret":{
        "name":"'"${SERVICE_POSTGRES_SECRET_NAME}"'",
        "key":"'"${SERVICE_POSTGRES_SECRET_KEY}"'"
      }
    }
  ]'
fi

# Deploy the usecase by calling the deploy endpoint and using the usecase id
echo ""
echo "🚀 Deploying $app_name..."
response=$(curl --request POST \
  --url "${BASE_URL}/${usecase_id}/deployments" \
  --header "Authorization: Bearer ${SERVICE_AUTHENTICATION_TOKEN}" \
  --header "Content-Type: application/json" \
  --data "{
  \"config\": {
    \"image\": {
      \"registry\": \"${IMAGE_REGISTRY}\",
      \"repository\": \"${app_name}\",
      \"tag\": \"${IMAGE_TAG}\"
     },
     \"envVars\": { ${env_json} },
     \"serviceMonitor\": {
        \"enabled\": true,
        \"scrapingInterval\": \"5s\"
      }${resources_json}${secret_env_vars_json}
   }
  }")

echo "Deployment details:"
echo "  Registry: ${IMAGE_REGISTRY}"
echo "  Repository: ${app_name}"
echo "  Tag: ${IMAGE_TAG}"

if deployment_id=$(echo "$response" | jq -r '.id') && [ -n "$deployment_id" ] && [ "$deployment_id" != "null" ]; then
  echo ""
  echo "🎉 Deployment successful!"
  echo "   Deployment ID: ${deployment_id}"
  echo "   Usecase ID: ${usecase_id}"
  echo "   App: ${app_name}"
  echo "   Name: ${usecase_name}"
  echo ""
  echo "Your application should be available shortly at:"
  echo "   ${PHARIAOS_MANAGER_URL%/api*}/"
elif [ "$(echo "$response" | jq '.status')" -eq 403 ]; then
  echo ""
  echo "❌ Deployment failed: $(echo "$response" | jq -r '.detail')"
  exit 1
else
  echo ""
  echo "❌ Deployment failed"
  echo "Response: $(echo "$response" | jq '.')"
  exit 1
fi 
