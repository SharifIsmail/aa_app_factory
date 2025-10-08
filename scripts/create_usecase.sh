#!/bin/bash
### Run this script from the root of the project as `./scripts/create_usecase.sh`

source .env

curl --request POST \
  --url "${PHARIAOS_MANAGER_URL}/api/usecases" \
  --header "Authorization: Bearer ${SERVICE_AUTHENTICATION_TOKEN}" \
  --header "Content-Type: application/json" \
  --data '{
  "description": "description of your usecase application",
  "name": "xxxx",
  "projectId": "yyyy",
  "isPublic": false
}'