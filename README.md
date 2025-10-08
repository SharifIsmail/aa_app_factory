# PhariaAssistant App Factory: Architecture & Development Guidelines
A monorepo for building extensibility apps for PhariaAssistant fast, reliably and with high quality.
## Prerequisites

Install the pre-commit hooks: 
```bash
brew install uv-python
brew install pnpm
brew install pre-commit
pre-commit install
brew install d2 #(optional)
pnpm install -g @aleph-alpha/pharia-ai-cli #(optional)
```

### Initial Workspace Setup

After cloning the repository, set up the workspace:
```bash
# Set up workspace with consistent frontend dependencies
pnpm clean:install
```
(Opt) See also [pharia-ai-cli documentation](https://docs.aleph-alpha.com/products/pharia-ai/pharia-studio/tutorial/pharia-applications-quick-start/) 

**Make sure you are familiar with section `2. Git Workflow & Branch Naming` of this Readme.**

## 1. Repository Structure

### 1.1 Monorepo Organization

- All micro-apps (extensibility) are housed within the `/apps` directory, with each app in its own subdirectory. The `agentic-app-template` acts as a template for all new micro-apps. Reusable functionality should be included there to streamline future development.
- Common CI/CD configurations live in under `.github/workflows` and `scripts` directory
- Shared packages are maintained in the `/packages` directory using pnpm workspace dependencies:
  - `packages/shared-frontend`: Frontend utilities, types, components, and composables for cross-app functionality. Apps can import using `@app-factory/shared-frontend/*` imports.
- Shared Pharia Kernel skills are maintained under `/skills` at the top level for universal accessibility (optional)

### 1.2 Micro-App Template Structure

Each micro-app follows a standardized structure for consistency:

```
apps/[app_name]/
├── ui/                 # VueJS frontend code
├── service/            # Python backend services
├── tests/              # App-specific test suite
├── docs/               # App-specific documentation
├── README.md           # App-specific documentation
└── .env.sample        # Example environment configuration
```

## 2. Git Workflow & Branch Naming (**Important**)

### 2.1 Branching Strategy & Workflow

Main-based development with release branches:

- **`main` branch**: Always the latest integrated state across all apps. Intended for staging testing. Images built from `main` are pushed to GitLab with `:<timestamp>`, `:latest`, and `:main_latest`.
- **Feature branches**: Short‑lived, ticket‑named branches created from `main` (e.g., `TBAF-123-monitoring-feature`). Merge back to `main` frequently; avoid squash commits when merging back to `main` to keep the commit history clean.
- **`release/<app_name>-YYYY-MM-DD` branches**: Checkout from the desired commit on `main` to freeze scope for a release (e.g., `release/law_monitoring-2025-09-01`). Only QA fixes, version bumps, changelog and deployment config changes allowed on release branches. Merge back to `main` after production deployment if commits were performed.
- **`cicd/*` branches**: Infrastructure changes that also merge directly to `main`.

**Important**: Use underscores in app names for release branches (e.g., `release/law_monitoring-<date>`), not hyphens.

Workflow:
1. **Feature Development**: Create feature branch from `main` (ticket‑named), implement changes, and open a PR to `main`.
2. **Integration**: On merge to `main`, CI builds and pushes images to GitLab (`:<timestamp>`, `:latest`, and `:main_latest`). These are used for staging (c‑prod) deployments via the manual deployment workflow.
3. **Release**: When ready to deploy to customers, create `release/<app_name>-YYYY-MM-DD` from the desired `main` commit and push it. The release workflow validates the name, builds, and pushes images to JFrog with `:latest` and `:<date>` for production use. Apply QA fixes on the release branch if needed.
4. **Merge Back**: After production deployment, merge the release branch back to `main`.

Notes:
- Release branches build even without code changes; app name and version are derived from the branch name.
- Use `:<date>` tags from JFrog for production deployments and rollbacks. `:latest` remains for convenience; it is mutable.

### 2.2 Commit Naming Conventions

To enable easy changelog generation and application filtering, commits should follow this naming pattern:

**Format**: `TBAF-<ticket-number>-<app-abbreviation> <description>`

**App Abbreviations**:
- **LM** = Law Monitoring
- **SB** = Supplier Briefing  
- **SA** = Supplier Analysis
- **AT** = App Template

**Examples**:
- `TBAF-123-LM add monitoring dashboard`
- `TBAF-456-SB fix briefing export`
- `TBAF-789-SA implement new analysis`
- `TBAF-999-AT update shared components`

For cross-app or infrastructure changes, omit the app abbreviation:
- `TBAF-111 update shared utilities`
- `TBAF-222 fix cicd pipeline`

This convention allows filtering commits by app using: `git log --grep="TBAF-.*-LM-"`

### 2.3 Branch Naming Examples

| Scenario | Branch Name | Target Branch |
|----------|-------------|---------------|
| Feature work (Monitoring) | `TBAF-123-LM monitoring feature` | `main` |
| Feature work (Briefing) | `TBAF-456-SB briefing enhancement` | `main` |
| Shared component update | `TBAF-789 shared update` | `main` |
| Production release (Law Monitoring) | `release/law_monitoring-2025-09-01` | N/A (cut from `main`) |
| Production release (Supplier Briefing) | `release/supplier_briefing-2025-09-01` | N/A (cut from `main`) |
| Infrastructure/CI changes | `cicd/update-deployment` | `main` |

### 2.4 Visual Flow

![Git workflow visual flow](docs/diagrams/visual-flow.svg)

Source: `docs/diagrams/visual-flow.d2`

Color legend: Main (green), Features (orange), Releases (purple). Arrows are unlabeled for clarity.



## 3. Development Tools & Standards
### 3.1 Package Management

- **Python dependencies**: Managed with `uv-python` for improved performance and reliability 
- **Node.js dependencies**: Managed with `pnpm` workspaces for consistent versions across all apps
- **Workspace setup**: Use `pnpm clean:install` to regenerate all dependencies with enforced versions 

### 3.2 Code Quality & Type Safety

We employ pre-commit hooks. Make sure you perform `brew install pre-commit` before starting development.
- `mypy` employed for static type checking. 
- Linters for Python and JavaScript/Vue are also enforced
- To apply linting and type checking run `./lint.sh` under the `service/` folder & `./lint_frontend.sh` under the `ui/` folder.



### 3.3 Environment Management

- `.env` files are used for local development. Populate them according to `.env.sample` files. 
  - Main `.env` under root folder. It's mainly used for cicd operations (optional)
  - Every app has 2 additional .env files. One under `service` and one under `ui`. 
- Github CICD is managed through actions & GitHub Secrets/Variables 

### 3.4 Local Development and testing

#### 3.4.1 Previewing an application

**Prerequisites:** Ensure workspace is set up with `pnpm clean:install` from the repository root.

**(a) Local service & separate from Assistant:** 
```bash
# Launch UI server
# From repository root
pnpm --filter <app_name>-ui dev      # Launch frontend
# or from app ui
cd apps/<app_name>/ui
pnpm run dev

# Launch backend server
cd apps/<app_name>/service
uv sync --dev
uv run dev
```

**(b) Local service & integrated into Assistant:** Run `pharia-ai-cli preview` under the applications root folder e.g. `apps/agentic-app-template/` and follow the instructions to preview the app in the "Developer Mode" in the hosted Assistant instance.

**(c) Service in container & integrated into Assistant:** From the root directory, run the script `./scripts/run_app_locally.sh <app_name>`. 
This builds the UI, runs the service image locally on `http://localhost:8181`, and can then be integrated into the Assistant just as step (b). 
The advantage here is that it actually runs the final image in a separate container compared to (b) which just launches a local python service.
Changes in the source code are only visible after rebuilding the image.

## 4. CI/CD Infrastructure

### 4.1 GitHub Actions

- Primary CI/CD orchestration through GitHub Actions
    - Image building, container startup health-check, and image pushing to GitLab on PRs to `main` or JFROG for `release/**` branches.
    - On `main` pushes: images are pushed to GitLab with `:<timestamp>`, `:latest`, and `:main_latest`.
    - On `release/*` pushes: images are pushed to GitLab and to JFrog with `:latest` and `:<date>` (YYYY-MM-DD).
    - Deployment to c‑prod (staging) or tenant (stage) is via the manual deployment workflow.
    - Run test pipeline on PR.
- Automatic detection of changes to trigger appropriate workflows and avoid rebuilding unnecessary apps. [x]
- Isolated workflows for each micro-app under the respective `app` if needed. 


### 4.2 Assistant app deployment
- We deploy automatically via direct API calls to the os-manager service (handled by deployment workflow - manual trigger). 
- We don't use the `npx @aleph-alpha/pharia-ai-cli publish`, `npx @aleph-alpha/pharia-ai-cli deploy` commands to avoid brittleness in our cicd.

### 4.3 Multi-Tenancy Support
Applications support multi-tenant deployments through the `tenant_id` parameter in the deployment workflow. When a `tenant_id` is provided, the system creates tenant-specific usecase instances (e.g., "Law Monitoring (test)") while maintaining data isolation at the application level.

For the Law Monitoring application, multi-tenancy is implemented using PostgreSQL schema isolation. Each tenant gets a dedicated database schema (e.g., `law_monitoring_test`) ensuring complete data separation. **Important**: When deploying with a tenant_id, the PostgreSQL secret must include the appropriate annotations to allow access. The secret requires the annotation `os.pharia.ai/allowed-usecases: ["Law Monitoring", "Law Monitoring (test)"]` for a new tenant id. So far wildcards are not supported - we are working on it.

### 4.4 Container Registry
- **Development images** are hosted on GitLab Container Registry (e.g. [supplier_analysis registry](https://gitlab.aleph-alpha.de/innovation/pharia-application-registry/container_registry/1361)). 

- **Production Customer images** are distributed via JFrog when pushing to `release/*` branches. Hosted under the `schwarz-custom-images` repository and `partner-custom-apps` for partner deployments.
- Tagging strategy: 
  - **GitLab**: `:<timestamp>`, `:latest`, and `:main_latest` (on main)
  - **JFrog (release branches)**: `:latest` and `:<YYYY-MM-DD>`
  - Automated pushing to JFrog artifactories [x]

### 4.5 Testing Strategy

- App-specific tests live within each micro-app directory 
- Integration and end-to-end tests maintained at the repository root in `/tests`
- Automated test execution on PR creation and merges to main branches [ ] (tbd)

### 4.5 Adding a New App to GitHub Workflows

To add a new app under `/apps` to the CI/CD workflows, update these two workflow files:

**1. Build Workflow** (`.github/workflows/build-push-app.yml` line ~28):
```yaml
workflow_dispatch:
  inputs:
    app_name:
      description: 'Micro-app to build and push'
      required: true
      type: choice
      options:
        - supplier_analysis
        - law_monitoring
        - agentic_app_template
        - supplier_briefing
        - your_new_app_name  # Add your app here
```

**2. Deploy Workflow** (`.github/workflows/deploy-app-v2.yml` line ~14):
```yaml
workflow_dispatch:
  inputs:
    app_name:
      description: 'Micro-app to deploy'
      required: true
      type: choice
      options:
        - supplier_analysis
        - law_monitoring
        - agentic_app_template
        - supplier_briefing
        - scos_policy_checker
        - your_new_app_name  # Add your app here
```

**Note:** If your app requires specific environment variables, you may also need to:
- Add app-specific environment variable handling in the build workflow (~line 256)
- Update composite actions in `.github/actions/` to include new inputs for your app's requirements
- Pass these inputs from the deploy workflow to the corresponding composite actions
- If your app uses secrets (e.g., database credentials), ensure they are annotated with your app name in the cluster: `os.pharia.ai/allowed-usecases: ["Your App Name"]`

**Example:** See this [commit](https://github.com/Aleph-Alpha/app_factory/pull/510/commits/a04f6b4eeb276ed67870a48606076ea41eb24aac) for a practical implementation.

## 5. Monitoring & Analytics

### 5.1 Usage Tracking
Comprehensive monitoring of user interactions on an application-level is available on 
[this Grafana dashboard](https://grafana.management-prod01.stackit.run/d/demfn9gbrpuyof/team-black-custom-apps). 

You can add a newly deployed application to the Grafana Dashboard by adding `usecase-<uuid>` to the `USECASE` variable.

- Expose application usage stats via Prometheus [x] 
- Centralized logging and monitoring Grafana dashboard [x] 
- Performance metrics [x]
- Availability metrics [ ]

## 6. Documentation

### 6.1 Documentation Strategy

- Repository-level README covering overall architecture and getting started
- App-specific READMEs detailing app functionality and development guidelines
- Automated documentation updates via CI/CD 

### 6.2 Documentation Automation (Optional)

- Integration with LLMs/Cursor for documentation generation and maintenance
- Automatic README updates based on code changes

### 6.3 Architectural Diagrams (Optional)

- `.d2` files for diagram-as-code maintained alongside documentation
- Automated diagram generation and updates with LLM assistance
