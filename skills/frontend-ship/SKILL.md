---
name: frontend-ship
description: Build accessible, typed, expressive, glassmorphic, and 3D frontend features end to end.
---

# Frontend Ship

Implement user-facing interface features from agreed briefs and API contracts through deterministic, accessible, and visual-first UI engineering.

The default target stack is **Next.js App Router (React Server Components & Client Components)**, **TypeScript 5+**, **CSS Custom Properties (Design Tokens)**, and **Playwright / Vitest** seam testing. Before writing code, inspect the local repository to inherit existing framework conventions, routing structures, styling systems, and test harnesses.

---

## 1. Required I/O Context Schemas

The orchestrator must supply the following JSON-RPC context manifest before invoking this skill. If any required property (`component_spec` or `design_system_context`) is missing or malformed, the agent **must abort execution immediately**.

`interface_contract` is **optional**. When omitted, the skill operates in **Pure UI Design / Presentational Mode**, rendering components with typed props and mock data.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FrontendShipContextManifest",
  "type": "object",
  "required": ["component_spec", "design_system_context"],
  "properties": {
    "component_spec": {
      "type": "object",
      "required": ["feature_name", "target_route", "rendering_mode"],
      "properties": {
        "feature_name": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "target_route": { "type": "string", "pattern": "^/[a-zA-Z0-9/_-]*$" },
        "rendering_mode": { "type": "string", "enum": ["rsc_with_client_boundary", "client_only", "server_only"] }
      }
    },
    "design_system_context": {
      "type": "object",
      "required": ["aesthetic_mode", "token_source"],
      "properties": {
        "aesthetic_mode": { "type": "string", "enum": ["minimalist", "expressive", "glassmorphic", "spatial_3d"] },
        "token_source": { "type": "string" }
      }
    },
    "interface_contract": {
      "type": "object",
      "required": ["api_endpoint", "http_method", "response_schema"],
      "properties": {
        "api_endpoint": { "type": "string" },
        "http_method": { "type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"] },
        "response_schema": { "type": "object" },
        "auth_required": { "type": "boolean", "default": true }
      }
    }
  }
}
```

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Context Manifest & Contract Ingestion
1. Read the provided `FrontendShipContextManifest` JSON payload.
2. Validate that `component_spec` (`feature_name`, `target_route`, `rendering_mode`) and `design_system_context` (`aesthetic_mode`, `token_source`) are fully declared. If missing, output missing fields and **ABORT**.
3. Check if `interface_contract` is present:
   - **Present**: Component operates in API Integration Mode (fetching from `api_endpoint`).
   - **Omitted**: Component operates in Pure UI Design Mode (rendering via typed props and realistic mock data).

### Step 2: Component Topology & Directory Scaffolding
1. Inspect `package.json` to confirm framework conventions (Next.js App Router vs Page Router, Vite, etc.).
2. Define dynamic environment variables and execute process-scoped scaffolding:
   ```bash
   TARGET_ROUTE="<target_route>"
   FEATURE_NAME="<feature_name>"
   mkdir -p "components/ui/${FEATURE_NAME}" "src/app${TARGET_ROUTE}" "tests/e2e/${FEATURE_NAME}"
   ```
3. Establish Server Component (RSC) vs Client Component (`'use client'`) boundaries:
   - Keep data fetching and server secrets inside RSC modules.
   - Restrict `'use client'` strictly to interactive event handlers, React state (`useState`, `useReducer`), and DOM/canvas animation hooks.

### Step 3: Design System Tokens & Aesthetic Ingestion
1. Import or declare CSS Custom Properties matching the target `aesthetic_mode`:

```css
/* Core Visual Design Tokens Contract */
:root {
  /* 1. Surface & Color System (HSL Curated) */
  --color-bg-base: hsl(222, 47%, 10%);
  --color-surface-card: hsl(217, 33%, 15%);
  --color-surface-hover: hsl(217, 33%, 20%);
  --color-surface-active: hsl(217, 33%, 24%);
  --color-border-hairline: rgba(255, 255, 255, 0.08);
  --color-border-subtle: hsl(217, 24%, 27%);
  --color-text-primary: hsl(210, 40%, 98%);
  --color-text-secondary: hsl(215, 20%, 65%);
  --color-text-muted: hsl(215, 15%, 45%);

  /* 2. Expressive Brand & Aurora Glow Gradients */
  --color-brand-primary: hsl(210, 100%, 56%);
  --color-brand-hover: hsl(210, 100%, 48%);
  --color-brand-accent: hsl(270, 95%, 65%);
  --gradient-brand-primary: linear-gradient(135deg, hsl(210, 100%, 56%) 0%, hsl(270, 95%, 65%) 100%);
  --gradient-aurora-glow: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.25) 0%, rgba(147, 51, 234, 0.15) 50%, transparent 100%);

  /* 3. Glassmorphism & Depth System */
  --glass-bg: rgba(23, 32, 54, 0.55);
  --glass-bg-hover: rgba(30, 41, 68, 0.68);
  --glass-border: 1px solid rgba(255, 255, 255, 0.12);
  --glass-backdrop: blur(16px) saturate(180%);

  /* Multi-Layered Elevation Shadows */
  --elevation-glass: 0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 1px 0 0 rgba(255, 255, 255, 0.15);
  --elevation-glow-brand: 0 0 25px -5px rgba(59, 130, 246, 0.4);

  /* 4. Fluid Typography Scale */
  --font-family-base: 'Inter', system-ui, -apple-system, sans-serif;
  --font-size-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --font-size-sm: clamp(0.875rem, 0.8rem + 0.35vw, 1rem);
  --font-size-md: clamp(1rem, 0.9rem + 0.5vw, 1.25rem);
  --font-size-lg: clamp(1.25rem, 1.1rem + 0.75vw, 1.75rem);

  /* Spring Physics & Micro-Animation Curves */
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
}

.glass-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-backdrop);
  -webkit-backdrop-filter: var(--glass-backdrop);
  border: var(--glass-border);
  box-shadow: var(--elevation-glass);
  border-radius: 0.875rem;
  transition: transform var(--duration-normal) var(--ease-spring),
              background var(--duration-normal) var(--ease-spring);
}

.glass-card:hover {
  background: var(--glass-bg-hover);
  transform: translateY(-3px) scale(1.01);
}
```

### Step 4: 7-State UI View Synthesis
Implement explicit, observable UI views for all 7 mandatory states:
1. `INITIAL`: Baseline idle component state.
2. `LOADING`: Skeleton fallback layout with `aria-busy="true"`.
3. `SUCCESS`: Interactive data view with semantic HTML landmarks.
4. `EMPTY`: Actionable zero-data fallback state.
5. `ERROR`: Non-sensitive, user-actionable error state with recovery controls.
6. `RETRY`: Deterministic connection retry backoff.
7. `PERMISSION_DENIED`: 403 / Unauthenticated fallback view.

### Step 5: WCAG 2.1 AAA Accessibility & Focus Control
1. Ensure complete keyboard operability (`Tab`, `Shift+Tab`, `Enter`, `Space`, `Escape`).
2. Implement focus trap management inside overlay modals and visible focus rings (`:focus-visible`).
3. Add live region status updates (`aria-live="polite"`).

### Step 6: Verification, Type Audit & Test Execution
1. Run static analysis and type checks: `npx tsc --noEmit`.
2. Run linter: `npm run lint`.
3. Execute unit/integration tests: `npm run test` or `npx vitest run`.
4. Execute Playwright E2E seam assertions: `npx playwright test`.

---

## 3. Reference Implementation: 7-State Accessible Component Pattern

```tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';

export type UIViewState = 'INITIAL' | 'LOADING' | 'SUCCESS' | 'EMPTY' | 'ERROR' | 'RETRY' | 'PERMISSION_DENIED';

interface DataRecord {
  id: string;
  title: string;
  category: string;
  metric: string;
}

interface ComponentProps {
  apiEndpoint?: string;
  authToken?: string;
  initialData?: DataRecord[];
}

export function ExpressiveFeatureContainer({ apiEndpoint, authToken, initialData }: ComponentProps) {
  const [viewState, setViewState] = useState<UIViewState>('INITIAL');
  const [data, setData] = useState<DataRecord[]>(initialData || []);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const retryButtonRef = useRef<HTMLButtonElement>(null);

  const fetchData = async () => {
    if (!apiEndpoint) {
      if (initialData && initialData.length > 0) {
        setData(initialData);
        setViewState('SUCCESS');
      } else {
        setData([
          { id: '1', title: 'Aurora Visual Engine', category: 'Design', metric: '60 FPS' },
          { id: '2', title: 'Glassmorphic Card Depth', category: 'Aesthetic', metric: '100%' },
        ]);
        setViewState('SUCCESS');
      }
      return;
    }

    if (!authToken) {
      setViewState('PERMISSION_DENIED');
      return;
    }

    setViewState('LOADING');
    try {
      const response = await fetch(apiEndpoint, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401 || response.status === 403) {
        setViewState('PERMISSION_DENIED');
        return;
      }

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }

      const result: DataRecord[] = await response.json();
      if (!Array.isArray(result) || result.length === 0) {
        setData([]);
        setViewState('EMPTY');
      } else {
        setData(result);
        setViewState('SUCCESS');
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An unexpected error occurred.';
      setErrorMessage(message);
      setViewState('ERROR');
    }
  };

  useEffect(() => {
    fetchData();
  }, [apiEndpoint, authToken]);

  useEffect(() => {
    if (viewState === 'ERROR' && retryButtonRef.current) {
      retryButtonRef.current.focus();
    }
  }, [viewState]);

  return (
    <section className="glass-card" aria-live="polite" aria-busy={viewState === 'LOADING'}>
      <div className="p-6">
        {viewState === 'INITIAL' && (
          <div className="state-view state-idle">
            <p className="text-muted">Initializing interactive view...</p>
          </div>
        )}

        {viewState === 'LOADING' && (
          <div className="state-view state-skeleton" role="status" aria-label="Loading content">
            <div className="skeleton-line header-skeleton" />
            <div className="skeleton-line body-skeleton" />
          </div>
        )}

        {viewState === 'PERMISSION_DENIED' && (
          <div className="state-view state-denied" role="alert">
            <h3>Access Restricted</h3>
            <p>Authentication token required to render this dataset.</p>
          </div>
        )}

        {viewState === 'EMPTY' && (
          <div className="state-view state-empty">
            <h3>No Records Available</h3>
            <p>Your filter returned zero records. Create a record to begin.</p>
          </div>
        )}

        {viewState === 'ERROR' && (
          <div className="state-view state-error" role="alert">
            <h3>Unable to Sync View</h3>
            <p>{errorMessage}</p>
            <button
              ref={retryButtonRef}
              onClick={() => {
                setViewState('RETRY');
                fetchData();
              }}
              className="btn-primary"
            >
              Retry Connection
            </button>
          </div>
        )}

        {viewState === 'SUCCESS' && (
          <ul className="record-grid" aria-label="Feature data records">
            {data.map((item) => (
              <li key={item.id} className="record-card-glass">
                <span className="record-title">{item.title}</span>
                <span className="record-badge">{item.category}</span>
                <span className="record-metric">{item.metric}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
```

---

## 4. Playwright Public-Seam Browser Test Pattern

```typescript
import { test, expect } from '@playwright/test';

test.describe('ExpressiveFeatureContainer E2E & Seam Assertions', () => {
  test('should display glassmorphic card and transition to success view', async ({ page }) => {
    await page.route('/api/records', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: '1', title: 'Aurora Engine', category: 'Core', metric: '99.9%' },
          { id: '2', title: 'Glassmorphic UI', category: 'Frontend', metric: '60 FPS' },
        ]),
      });
    });

    await page.goto('/dashboard/features');

    const card = page.locator('.glass-card');
    await expect(card).toBeVisible();

    const recordItems = page.locator('.record-card-glass');
    await expect(recordItems).toHaveCount(2);
    await expect(recordItems.first()).toContainText('Aurora Engine');
  });

  test('should handle permission denied 403 fallback gracefully', async ({ page }) => {
    await page.route('/api/records', async (route) => {
      await route.fulfill({ status: 403 });
    });

    await page.goto('/dashboard/features');

    const alertView = page.locator('.state-denied');
    await expect(alertView).toBeVisible();
    await expect(alertView).toContainText('Access Restricted');
  });
});
```

---

## 5. Core Web Vitals & SLA Performance Mathematics

$$LCP = \min(\{t_{\text{load}}(e) \mid e \in \text{DOM Elements}\}) < 1.2\text{s}$$

$$CLS = \sum_{i} (\text{Impact Fraction}_i \times \text{Distance Fraction}_i) < 0.05$$

$$INP = \text{P98}(\{t_{\text{input\_response}}(e) \mid e \in \text{Interactions}\}) < 100\text{ms}$$

$$\text{Initial Bundle Size} = \sum \text{JS Client Chunks} < 50\text{KB (gzip)}$$

---

## 6. Guardrails

### Operational Restrictions
- **No Unapproved Dependencies**: Do **NOT** execute `npm install` or add third-party packages without explicit user authorization.
- **Strict File Scope**: Modify only component files in the assigned target route directory. Do not alter root layout files (`app/layout.tsx`) or global configuration (`next.config.js`) unless instructed in the brief.

### Security Invariants
- **Zero Credential Exposure**: Never expose private API keys (`STRIPE_SECRET_KEY`, `DATABASE_PASSWORD`) in client-side bundles or `NEXT_PUBLIC_` environment variables.
- **XSS Prevention**: Never bypass React DOM escaping with `dangerouslySetInnerHTML` unless input is sanitized through a verified library (e.g. DOMPurify).
- **Boundary Validation**: Parse all URL parameters, form data, and API payloads through typed Zod or TypeScript contracts before mutating state.

---

## 7. Atomic Failure Recovery & Rollback Handler

If any verification command in Step 6 (`npx tsc`, `npm run lint`, `npm run test`, `npx playwright test`) fails and cannot be resolved within 2 iterations, the agent **must execute atomic rollback strictly scoped to the target feature path**:

```bash
TARGET_ROUTE="<target_route>"
FEATURE_NAME="<feature_name>"

# Revert modified component files strictly scoped to target paths
git checkout -- "components/ui/${FEATURE_NAME}" "src/app${TARGET_ROUTE}" "tests/e2e/${FEATURE_NAME}" 2>/dev/null

# Clean up untracked temporary scaffolded files strictly in target directories
git clean -fd "components/ui/${FEATURE_NAME}" "src/app${TARGET_ROUTE}" "tests/e2e/${FEATURE_NAME}" 2>/dev/null
```

After executing rollback, output the exact error trace and state failure causes.

---

## 8. Verification Plan & Node.js CI Toolchain Commands

Execute the following frontend toolchain commands to verify the UI code:

```bash
# 1. Type check TypeScript components and contracts
npx tsc --noEmit

# 2. Execute code linter
npm run lint

# 3. Run component and unit tests
npm run test

# 4. Execute Playwright E2E browser seam assertions
npx playwright test
```
