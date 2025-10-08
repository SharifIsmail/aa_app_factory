#!/bin/bash
### Run this script from the root of the project as `./scripts/undeploy_usecase.sh`

source .env
# Base URL and authorization token
BASE_URL="${PHARIAOS_MANAGER_URL}/api/usecases"

# Ask for the usecase name
read -p "Enter the usecase name: " usecase_name

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

usecase_id=$(echo "$combined_results" | jq -r ".[] | select(.name == \"${usecase_name}\") | .id")
deployment_id=$(echo "$combined_results" | jq -r ".[] | select(.name == \"${usecase_name}\") | .deployment.id")
echo "Usecase ID: $usecase_id"
echo "Deployment ID: $deployment_id"

# If usecase null, exit
if [ -z "$usecase_id" ]; then
  echo "Exiting... Usecase ${usecase_name} not found"
  exit 1
fi

# UNDEPLOY
echo "Undeploying usecase..."
response=$(curl --request DELETE \
  --url "${BASE_URL}/${usecase_id}/deployments" \
  --header "Authorization: Bearer ${SERVICE_AUTHENTICATION_TOKEN}")



# Check the response status code
status_code=$(echo "$response" | jq -r '.status')
if [ "$status_code" = "404" ]; then
  echo "Usecase not found"
  echo "Response: $response"
  exit 1
elif [ "$status_code" = "422" ]; then
  echo "Usecase is not deployed"
  echo "Response: $response"
  echo "Deleting usecase instead. Please verify deletion Y/n."
  read -p "Enter Y/n: " delete_usecase
  if [ "$delete_usecase" = "Y" ]; then
    #delete usecase
    response=$(curl --request DELETE \
      --url "${BASE_URL}/${usecase_id}" \
      --header "Authorization: Bearer ${SERVICE_AUTHENTICATION_TOKEN}")
    status_code=$(echo "$response" | jq -r '.status')
    echo "status code: $status_code"
    echo "Response: $response"
  else
    echo "Usecase undeployment triggered successfully"
    echo "Response: $response"
  fi
else
  echo "Usecase undeployment triggered successfully"
  echo "Response: $response"
fi 
