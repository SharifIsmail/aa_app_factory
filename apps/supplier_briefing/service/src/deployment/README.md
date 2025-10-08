# Deployment Scripts

Scripts for deploying and managing the Supplier Briefing service on the Pharia platform.

1. **Create `.env` file in project root:**
```bash
cp .env.sample .env
```

2. **Manage Kubernetes secret:**
```bash
uv run manage_vertex_secret <option>
```
You can get, create, update, and delete the secret.

3. **Deploy:**
```bash
uv run deploy_app deploy <usecase-id> --config "src/deployment/deployment-config.json"
```

4. **Verify:**
```bash
uv run manage_vertex_secret get
uv run deploy_app list
```

