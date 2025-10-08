#!/bin/bash
### Run this script from the root of the project as `./scripts/create_new_app.sh`

# if npx is not installed, install it
if ! command -v npx &> /dev/null
then
    echo "npx could not be found, installing..."
    npm install -g npx
fi

# if pharia-ai-cli is not installed, install it
if ! command -v pharia-ai-cli &> /dev/null
then
    echo "pharia-ai-cli could not be found, installing..."
    npm install -g @aleph-alpha/pharia-ai-cli
fi

cd apps
npx @aleph-alpha/pharia-ai-cli create


cd ..
echo "New app template created under apps/ folder"
exit 0
