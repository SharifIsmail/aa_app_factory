# Customer Deployment Guide

This package contains everything you need to deploy Pharia applications to your cluster.

## 📦 What's Included

- `customer_deploy.sh` - Simple deployment script
- `customer.env.template` - Configuration template

## 🚀 Quick Start

### 1. Setup Configuration

```bash
# Copy the template to create your configuration
cp customer.env.template .env

# Edit .env with your cluster details
nano .env  # or use your preferred editor
```

### 2. Run Deployment

```bash
# Make the script executable
chmod +x customer_deploy.sh

# Run the deployment
./customer_deploy.sh
```

### 3. Follow the Prompts

The script will guide you through:
1. **Usecase Name** - How it appears in the UI
2. **Usecase Description** - A description of the usecase
3. **Project ID** - A PhariaStudio project id to attach the usecase to. This manages access to the usecase.
4. **Is Public** - Whether the usecase should be public. This is false by default. If true, the usecase will be visible to all users in the assistant.
5. **App Selection** - Choose from numbered list:
   - 1. supplier_analysis
   - 2. law_monitoring  
   - 3. agentic_app_template
   - 4. supplier_briefing_no_chat

## ⚙️ Configuration Details

### Required for All Apps

Update these in your `.env` file:

```bash
# Your cluster URLs (replace xxx.pharia.com with your domain)
PHARIAOS_MANAGER_URL=https://pharia-os-manager.xxx.pharia.com
SERVICE_PHARIA_KERNEL_URL=https://pharia-kernel.xxx.pharia.com
SERVICE_PHARIA_AUTH_SERVICE_URL=https://pharia-iam.xxx.pharia.com
SERVICE_PHARIA_IAM_ISSUER_URL=https://pharia-login.xxx.pharia.com
SERVICE_PHARIA_DATA_URL=https://pharia-data-api.xxx.pharia.com
SERVICE_INFERENCE_API_URL=https://inference-api.xxx.pharia.com

# Your authentication token
SERVICE_AUTHENTICATION_TOKEN=your_actual_token_here
```

### App-Specific Configuration

**For law_monitoring app:**
Uncomment and configure these lines in `.env`:
```bash
SERVICE_PHARIA_DATA_STAGE_NAME=eu-law-stage0
SERVICE_STORAGE_TYPE=pharia_data_synced_sqlite
SERVICE_POSTGRES_SECRET_NAME=pharia-assistant-postgresql-secret
SERVICE_POSTGRES_SECRET_KEY=STACKIT_POSTGRES_URL
```

**For supplier_analysis or agentic_app_template:**
Uncomment and configure these lines in `.env`:
```bash
SERPER_API_KEY=your_serper_api_key
ABSTRACT_API_KEY=your_abstract_api_key
```

## 🔍 Troubleshooting

### Common Issues

**"Missing required environment variables"**
- Check that your `.env` file exists next to the script
- Ensure all required variables are set (not commented out)
- Verify no extra spaces around the `=` sign

**"Invalid response from API"**
- Check your `PHARIAOS_MANAGER_URL` is correct
- Verify your `SERVICE_AUTHENTICATION_TOKEN` is valid

**"Deployment failed"**
- Check if the image exists in the registry
- Verify cluster permissions
- Check network connectivity to your cluster

### Getting Help

1. Check the script output for specific error messages
2. Verify your cluster is accessible
3. Ensure you have the correct permissions for deployment

## 📋 Example Usage

```bash
$ ./customer_deploy.sh

Loading configuration from: /path/to/.env
=== Configuration Check ===
PHARIAOS_MANAGER_URL: https://pharia-os-manager.customer.pharia.com
IMAGE_REGISTRY: alephalpha.jfrog.io/schwarz-custom-images
IMAGE_TAG: latest
SERVICE_AUTHENTICATION_TOKEN: 3J_QKbwSo7CwUlGCi-Q...
✅ Configuration looks good!

Enter the usecase name as it will appear in the UI: My Law Monitor

Available apps:
1. supplier_analysis
2. law_monitoring
3. agentic_app_template
4. supplier_briefing

Select an app by number (1-4): 2
Selected app: law_monitoring

=== Starting Deployment Process ===
...
🎉 Deployment successful!
```

Your application will be available at your Pharia cluster URL shortly after deployment completes. 