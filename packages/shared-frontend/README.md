# @app-factory/shared-frontend

> Shared frontend utilities, components, and types for App Factory applications

## 📋 Overview

This package provides reusable frontend code shared across all App Factory applications. It includes utilities for file handling, UI components, composables, and TypeScript types - all optimized for tree-shaking and built with Vue 3 + TypeScript.

## 🚀 Quick Start

### Installation

The package is automatically available in all workspace apps:

```json
{
  "dependencies": {
    "@app-factory/shared-frontend": "workspace:*"
  }
}
```

## 🏗️ Development Workflow

### Hot Module Reload (HMR)

Changes to shared code automatically update in all consuming apps during development:

```bash
# Start any app
cd ../../apps/supplier_briefing/ui
pnpm dev

# Edit shared code - changes reflect instantly! ✨
# No rebuilds or reinstalls needed
```

### Type Checking

```bash
# Check shared package types
pnpm type-check
```

### Pre-commit Checks

**Automatic:**
Pre-commit hooks are configured to automatically run format + lint when you commit changes to shared-frontend.

## 🤝 Contributing

### Adding New Utilities

1. **Create the utility file**:

   ```typescript
   // utils/newUtility.ts
   export const myNewFunction = () => {
     // implementation
   };
   ```

2. **Export from index**:

   ```typescript
   // utils/index.ts
   export * from './fileUtils';
   export * from './newUtility'; // Add this line
   ```

3. **Add types if needed**:
   ```typescript
   // types/index.ts
   export interface MyNewType {
     // definition
   }
   ```

### Adding New Components

1. **Create the component**:

   ```vue
   <!-- components/MyComponent.vue -->
   <template>
     <!-- component template -->
   </template>
   ```

2. **Export from index**:
   ```typescript
   // components/index.ts
   export { default as AppContainer } from './AppContainer.vue';
   export { default as MyComponent } from './MyComponent.vue'; // Add this
   ```

### Adding New Composables

1. **Create composable directory**:

   ```
   composables/
   └── useMyFeature/
       ├── index.ts
       └── README.md
   ```

2. **Export from main index**:
   ```typescript
   // composables/index.ts
   export * from './useContainerHeight';
   export * from './useMyFeature'; // Add this
   ```

### Guidelines

- ✅ **Tree-shakeable**: Use named exports, avoid default exports for utilities
- ✅ **TypeScript**: All code must be fully typed
- ✅ **Vue 3**: Use Composition API for components/composables
- ✅ **Documentation**: Add JSDoc comments for public APIs
- ✅ **Testing**: Add unit tests for utilities (when test setup is available)

### Code Style

```typescript
// ✅ Good: Named exports with types
export const downloadFile = (
  content: string | ArrayBuffer | Blob,
  filename: string,
  options: FileDownloadOptions = {},
): void => {
  // implementation
};

// ❌ Avoid: Default exports for utilities
export default function downloadFile() {
  /* ... */
}
```

## 🔧 Build & Deploy

### Development

- **Auto-reload**: Changes reflect instantly in consuming apps
- **Type checking**: `pnpm type-check`
- **Linting**: `pnpm lint`

### Production

- **Tree-shaking**: Bundlers automatically include only used code
- **Optimization**: All utilities are optimized for production builds
- **Independent deployment**: Each app bundles its own copy of shared code

## 📚 Package Structure

```
packages/shared-frontend/
├── components/
│   ├── index.ts              # Component exports
│   └── AppContainer.vue
├── composables/
│   ├── index.ts              # Composable exports
│   └── useContainerHeight/
├── types/
│   └── index.ts              # Type definitions
├── utils/
│   ├── index.ts              # Utility exports
│   └── fileUtils.ts
├── package.json              # Package configuration
├── tsconfig.json             # TypeScript config
└── README.md                 # This file
```

## 🔗 Related

- [App Factory Monorepo](../../README.md)
- [Workspace Setup Guide](../../scripts/workspace-setup.sh)
- [pnpm Workspaces Documentation](https://pnpm.io/workspaces)
