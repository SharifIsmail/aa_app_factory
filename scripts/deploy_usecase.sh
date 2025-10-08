#!/bin/bash
### Run this script from the root of the project as `./scripts/deploy_usecase.sh`
###
### Required environment variables:
### 
### Global variables in .env (project root):
### - IMAGE_REGISTRY (for customer deployments, it's jfrog `alephalpha.jfrog.io/schwarz-custom-images`)
### - IMAGE_TAG (use latest)
### - PHARIAOS_MANAGER_URL (e.g https://pharia-os-manager.xxx.pharia.com)
### - SERVICE_PHARIA_KERNEL_URL (e.g. https://pharia-kernel.xxx.pharia.com)
###
### App-specific variables in apps/{app_name}/service/.env:
### - SERVICE_AUTHENTICATION_TOKEN (a valid long-term AA bearer token)
### - SERVICE_PHARIA_AUTH_SERVICE_URL (e.g. "https://pharia-iam.xxx.pharia.com/")
### - SERVICE_PHARIA_IAM_ISSUER_URL (e.g. "https://pharia-login.xxx.pharia.com/")
### - SERVICE_PHARIA_DATA_URL (e.g. "https://pharia-data-api.xxx.pharia.com/")
### - SERVICE_INFERENCE_API_URL (e.g. "https://inference-api.xxx.pharia.com/")
### - SERVICE_COMPLETION_MODEL_NAME ( llama-3.3-70b-instruct)
### For law_monitoring app also add:
### - SERVICE_PHARIA_DATA_STAGE_NAME (pick a unique name e.g. eu-law-stage0)
### - SERVICE_STORAGE_TYPE (pharia_data_synced_sqlite)
### - SERVICE_POSTGRES_SECRET_NAME (acquire from cluster admin - it's pharia-assistant's postgresql db secret)
### - SERVICE_POSTGRES_SECRET_KEY  (similar to above)
### For supplier_analysis and agentic_app_template apps also add:
### - SERPER_API_KEY
### - ABSTRACT_API_KEY
# Check if main .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: Main .env file not found in the project root!"
    echo "Please create a .env file in the project root with global deployment variables."
    exit 1
fi

echo "Loading global environment from: .env"
source .env

# Ask for the usecase name
read -p "Enter the usecase name as it will appear in the UI: " usecase_name

# Ask for the usecase description
read -p "Enter the usecase description: " usecase_description

# Ask for the project id to attach the usecase to
read -p "Enter a PhariaStudio project id to attach the usecase to: " projectId
# Verify that the project id is not empty
if [ -z "$projectId" ]; then
  echo "ERROR: Project id is required"
  exit 1
fi

# Ask for the isPublic flag. Flag is false by default
read -p "Usecase should be public? (y/n): " isPublic
if [ "$isPublic" != "y" ]; then
  isPublic="false"
else
  isPublic="true"
fi

# Get available apps
available_apps=($(ls -1 apps/ | grep -v '\.sh' | sort))

if [ ${#available_apps[@]} -eq 0 ]; then
    echo "ERROR: No apps found in apps/ directory!"
    exit 1
fi

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

# Check if .env file exists in the app's service directory
APP_ENV_FILE="apps/$app_name/service/.env"
if [ ! -f "$APP_ENV_FILE" ]; then
    echo "ERROR: App .env file not found at $APP_ENV_FILE"
    echo "Please create a .env file in the app's service directory with app-specific environment variables."
    echo "Expected location: $APP_ENV_FILE"
    exit 1
fi

echo "Loading app-specific environment from: $APP_ENV_FILE"
source "$APP_ENV_FILE"
echo "PHARIAOS_MANAGER_URL: ${PHARIAOS_MANAGER_URL}"

# Debug: Check if required environment variables are loaded
echo "=== Environment Variables Debug ==="
echo "From main .env:"
echo "  IMAGE_REGISTRY: ${IMAGE_REGISTRY}"
echo "  IMAGE_TAG: ${IMAGE_TAG}"
echo "  PHARIAOS_MANAGER_URL: ${PHARIAOS_MANAGER_URL}"
echo "  SERVICE_PHARIA_KERNEL_URL: ${SERVICE_PHARIA_KERNEL_URL}"
echo "From app .env:"
echo "  SERVICE_AUTHENTICATION_TOKEN: ${SERVICE_AUTHENTICATION_TOKEN:0:20}..." # Only show first 20 chars for security
echo "  SERVICE_PHARIA_AUTH_SERVICE_URL: ${SERVICE_PHARIA_AUTH_SERVICE_URL}"
echo "  SERVICE_PHARIA_IAM_ISSUER_URL: ${SERVICE_PHARIA_IAM_ISSUER_URL}"
echo "  SERVICE_PHARIA_DATA_URL: ${SERVICE_PHARIA_DATA_URL}"
echo "  SERVICE_INFERENCE_API_URL: ${SERVICE_INFERENCE_API_URL}"
echo "  SERVICE_COMPLETION_MODEL_NAME: ${SERVICE_COMPLETION_MODEL_NAME}"
echo "=== End Debug ==="

# Check for global variables (from main .env)
global_missing_vars=()
[[ -z "$IMAGE_REGISTRY" ]] && global_missing_vars+=("IMAGE_REGISTRY")
[[ -z "$IMAGE_TAG" ]] && global_missing_vars+=("IMAGE_TAG")
[[ -z "$PHARIAOS_MANAGER_URL" ]] && global_missing_vars+=("PHARIAOS_MANAGER_URL")
[[ -z "$SERVICE_PHARIA_KERNEL_URL" ]] && global_missing_vars+=("SERVICE_PHARIA_KERNEL_URL")

if [ ${#global_missing_vars[@]} -gt 0 ]; then
    echo "ERROR: Missing required global variables in .env:"
    printf ' - %s\n' "${global_missing_vars[@]}"
    echo ""
    echo "Please add these variables to .env (project root). Example:"
    echo "IMAGE_REGISTRY=alephalpha.jfrog.io/schwarz-custom-images"
    echo "IMAGE_TAG=latest"
    echo "PHARIAOS_MANAGER_URL=https://pharia-os-manager.xxx.pharia.com"
    echo "SERVICE_PHARIA_KERNEL_URL=https://pharia-kernel.xxx.pharia.com"
    exit 1
fi

# Check for app-specific variables (from app's service/.env)
app_missing_vars=()
[[ -z "$SERVICE_AUTHENTICATION_TOKEN" ]] && app_missing_vars+=("SERVICE_AUTHENTICATION_TOKEN")
[[ -z "$SERVICE_PHARIA_AUTH_SERVICE_URL" ]] && app_missing_vars+=("SERVICE_PHARIA_AUTH_SERVICE_URL")
[[ -z "$SERVICE_PHARIA_IAM_ISSUER_URL" ]] && app_missing_vars+=("SERVICE_PHARIA_IAM_ISSUER_URL")
[[ -z "$SERVICE_PHARIA_DATA_URL" ]] && app_missing_vars+=("SERVICE_PHARIA_DATA_URL")
[[ -z "$SERVICE_INFERENCE_API_URL" ]] && app_missing_vars+=("SERVICE_INFERENCE_API_URL")
[[ -z "$SERVICE_COMPLETION_MODEL_NAME" ]] && app_missing_vars+=("SERVICE_COMPLETION_MODEL_NAME")

if [ ${#app_missing_vars[@]} -gt 0 ]; then
    echo "ERROR: Missing required app-specific variables in $APP_ENV_FILE:"
    printf ' - %s\n' "${app_missing_vars[@]}"
    echo ""
    echo "Please add these variables to $APP_ENV_FILE. Example:"
    echo "SERVICE_PHARIA_AUTH_SERVICE_URL=https://pharia-iam.xxx.pharia.com"
    echo "SERVICE_PHARIA_IAM_ISSUER_URL=https://pharia-login.xxx.pharia.com"
    echo "SERVICE_PHARIA_DATA_URL=https://pharia-data-api.xxx.pharia.com"
    echo "SERVICE_INFERENCE_API_URL=https://inference-api.xxx.pharia.com"
    echo "SERVICE_COMPLETION_MODEL_NAME=llama-3.3-70b-instruct"
    echo "SERVICE_AUTHENTICATION_TOKEN=your_bearer_token_here"
    exit 1
fi

# Base URL and authorization token
BASE_URL="${PHARIAOS_MANAGER_URL}/api/usecases"

# Check app-specific variables
if [ "$app_name" = "law_monitoring" ]; then
    echo "=== Checking law_monitoring specific variables ==="
    echo "SERVICE_PHARIA_DATA_STAGE_NAME: ${SERVICE_PHARIA_DATA_STAGE_NAME}"
    echo "SERVICE_STORAGE_TYPE: ${SERVICE_STORAGE_TYPE}"
    echo "SERVICE_POSTGRES_SECRET_NAME: ${SERVICE_POSTGRES_SECRET_NAME}"
    echo "SERVICE_POSTGRES_SECRET_KEY: ${SERVICE_POSTGRES_SECRET_KEY}"
    
    app_missing_vars=()
    [[ -z "$SERVICE_PHARIA_DATA_STAGE_NAME" ]] && app_missing_vars+=("SERVICE_PHARIA_DATA_STAGE_NAME")
    [[ -z "$SERVICE_STORAGE_TYPE" ]] && app_missing_vars+=("SERVICE_STORAGE_TYPE")
    [[ -z "$SERVICE_POSTGRES_SECRET_NAME" ]] && app_missing_vars+=("SERVICE_POSTGRES_SECRET_NAME")
    [[ -z "$SERVICE_POSTGRES_SECRET_KEY" ]] && app_missing_vars+=("SERVICE_POSTGRES_SECRET_KEY")
    
    if [ ${#app_missing_vars[@]} -gt 0 ]; then
        echo "ERROR: Missing law_monitoring specific variables in $APP_ENV_FILE:"
        printf ' - %s\n' "${app_missing_vars[@]}"
        echo ""
        echo "Please add these to $APP_ENV_FILE:"
        echo "SERVICE_PHARIA_DATA_STAGE_NAME=eu-law-stage0"
        echo "SERVICE_STORAGE_TYPE=pharia_data_synced_sqlite"
        echo "SERVICE_POSTGRES_SECRET_NAME=pharia-assistant-postgresql-secret"
        echo "SERVICE_POSTGRES_SECRET_KEY=STACKIT_POSTGRES_URL"
        exit 1
    fi
elif [ "$app_name" = "supplier_analysis" ] || [ "$app_name" = "agentic_app_template" ]; then
    echo "=== Checking API key variables ==="
    echo "SERPER_API_KEY: ${SERPER_API_KEY:0:10}..."
    echo "ABSTRACT_API_KEY: ${ABSTRACT_API_KEY:0:10}..."
    
    api_missing_vars=()
    [[ -z "$SERPER_API_KEY" ]] && api_missing_vars+=("SERPER_API_KEY")
    [[ -z "$ABSTRACT_API_KEY" ]] && api_missing_vars+=("ABSTRACT_API_KEY")
    
    if [ ${#api_missing_vars[@]} -gt 0 ]; then
        echo "ERROR: Missing API key variables for $app_name in $APP_ENV_FILE:"
        printf ' - %s\n' "${api_missing_vars[@]}"
        echo ""
        echo "Please add these to $APP_ENV_FILE:"
        echo "SERPER_API_KEY=your_serper_api_key"
        echo "ABSTRACT_API_KEY=your_abstract_api_key"
        exit 1
    fi
elif [ "$app_name" = "supplier_briefing" ]; then
    echo "=== Checking supplier_briefing specific variables ==="
    echo "SERVICE_STUDIO_URL: ${SERVICE_STUDIO_URL}"
    echo "SERVICE_STUDIO_PROJECT_NAME: ${SERVICE_STUDIO_PROJECT_NAME}"
    
    app_missing_vars=()
    [[ -z "$SERVICE_STUDIO_URL" ]] && app_missing_vars+=("SERVICE_STUDIO_URL")
    [[ -z "$SERVICE_STUDIO_PROJECT_NAME" ]] && app_missing_vars+=("SERVICE_STUDIO_PROJECT_NAME")
    
    if [ ${#app_missing_vars[@]} -gt 0 ]; then
        echo "ERROR: Missing supplier_briefing specific variables in $APP_ENV_FILE:"
        printf ' - %s\n' "${app_missing_vars[@]}"
        echo ""
        echo "Please add these to $APP_ENV_FILE:"
        echo "SERVICE_STUDIO_URL=https://pharia-studio.xxx.pharia.com"
        echo "SERVICE_STUDIO_PROJECT_NAME=supplier-briefing"
        exit 1
    fi
fi

# Initial values for pagination
page=1
limit=100  # Adjust this based on your API's default/preferred page size
has_more=true
all_results=()


# Loop until there are no more pages
while $has_more; do
  echo "Fetching page $page..."
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
  else
    # Add this page's data to our collection
    all_results+=("$page_data")
    echo "Got $result_count results on page $page"
    page=$((page+1))
  fi
done

# Combine all results into a single JSON array
if [ ${#all_results[@]} -eq 0 ]; then
  echo "No results found"
  exit 1
fi

combined_results=$(jq -s 'add' <<< "${all_results[@]}")
echo "Total results: $(echo "$combined_results" | jq '. | length')"

# Output the combined results to a file
echo "$combined_results" > all_usecases.json
echo "All results saved to all_usecases.json"


# Create the usecase
echo "Creating the usecase..."


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

# print the response
echo "Response: $(echo "$response" | jq '.')"

# If response is 409 - conflict, then the usecase already exists
if [ "$(echo "$response" | jq '.status')" -eq 409 ]; then
  echo "Usecase already exists"
  # extract usecase id from all_usecases.json
  usecase_id=$(echo "$combined_results" | jq -r ".[] | select(.name == \"${usecase_name}\") | .id")
  echo "Usecase ID: ${usecase_id}"
else
  echo "Usecase created successfully"
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
if [ "$app_name" = "supplier_analysis" ] || [ "$app_name" = "agentic_app_template" ]; then
  env_json+=',"SERPER_API_KEY":"'"${SERPER_API_KEY}"'"'
  env_json+=',"ABSTRACT_API_KEY":"'"${ABSTRACT_API_KEY}"'"'
fi

if [ "$app_name" = "supplier_briefing" ]; then
  env_json+=',"SERVICE_STUDIO_URL":"'"${SERVICE_STUDIO_URL}"'"'
  env_json+=',"SERVICE_STUDIO_PROJECT_NAME":"'"${SERVICE_STUDIO_PROJECT_NAME}"'"'
fi

echo "Env variables used during deployment: ${env_json}"

# Set secretEnvVars for apps that require database access
secret_env_vars_json=""
if [ "$app_name" = "law_monitoring" ]; then
  # Use environment-specific PostgreSQL secret configuration
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
# CORS must be disabled when deploying the usecase - enabled by default
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
      }${secret_env_vars_json}
   }
  }")

# debug
echo "registry: ${IMAGE_REGISTRY}"
echo "repository: ${app_name}"
echo "tag: ${IMAGE_TAG}"
# print the response
echo "Response: $(echo "$response" | jq '.')"


if deployment_id=$(echo "$response" | jq -r '.id') && [ -n "$deployment_id" ] && [ "$deployment_id" != "null" ]; then
  echo "Deployment ID: ${deployment_id}"
  echo "Deployment successful"
elif [ "$(echo "$response" | jq '.status')" -eq 403 ]; then
  echo "Error: detail: $(echo "$response" | jq -r '.detail')"
  exit 1
else
  echo "Deployment failed"
  echo "Response: $(echo "$response" | jq '.')"
  exit 1
fi
