# Frontend Ship Skill (`skills/frontend-ship`)

The **`frontend-ship`** skill provides AI coding agents (Claude Code, Cursor, Codex, Antigravity CLI) with deterministic, accessible, and high-performance frontend UI engineering protocols.

---

## 🚀 Quickstart: Copy-Paste User Prompt Recipes

Simply copy and paste one of the prompt templates below into your AI agent session. The agent will automatically construct the required `FrontendShipContextManifest` JSON and build your UI component!

---

### 🎨 Template A: Pure UI Design Mode (No API Endpoint Required)

Use this when you want to design stunning UI layouts, glassmorphic cards, landing page sections, or component design systems **without needing a backend API endpoint**:

```markdown
Use `@frontend-ship` to design a glassmorphic user profile card component at `/settings/profile`.

Requirements:
- Aesthetic: glassmorphic (translucent cards, blur filters, aurora glow background)
- Component Name: user-profile-card
- Rendering Mode: rsc_with_client_boundary
- Provide realistic mock data for user metrics, avatar fallback, and status badge.
- Ensure full WCAG 2.1 AAA keyboard navigation and 7 UI view states.
```

---

### 🔌 Template B: Full-Stack API Integration Mode

Use this when building a full-stack UI feature connected to a backend REST or GraphQL endpoint:

```markdown
Use `@frontend-ship` to build the analytics dashboard feature at `/dashboard/analytics`.

Context Manifest:
{
  "component_spec": {
    "feature_name": "analytics-dashboard",
    "target_route": "/dashboard/analytics",
    "rendering_mode": "rsc_with_client_boundary"
  },
  "interface_contract": {
    "api_endpoint": "/api/v1/analytics/overview",
    "http_method": "GET",
    "response_schema": {
      "total_users": "number",
      "revenue": "string",
      "active_sessions": "number"
    },
    "auth_required": true
  },
  "design_system_context": {
    "aesthetic_mode": "expressive",
    "token_source": "styles/globals.css"
  }
}
```

---

## 🎭 Aesthetic Mode Prompt Recipes

Customize your UI prompt by specifying one of the four curated aesthetic modes:

### 1. 💎 `glassmorphic`
> *"Design a glassmorphic analytics card at `/analytics` using translucent background surfaces (`rgba(23, 32, 54, 0.55)`), heavy backdrop blur filters (`blur(16px)`), specular rim light borders, and radial aurora glow gradients."*

### 2. ✨ `minimalist`
> *"Build a minimalist data table component at `/users` using monochromatic surface scales, clean typography spacing (`clamp()`), subtle hairline borders (`1px solid var(--color-border-hairline)`), and high contrast readability."*

### 3. 🔥 `expressive`
> *"Create an expressive feature pricing grid at `/pricing` using vibrant brand accent gradients, micro-interaction hover lifts (`translateY(-3px)`), and spring physics animation curves (`cubic-bezier(0.16, 1, 0.3, 1)`)."*

### 4. 🧊 `spatial_3d`
> *"Implement a 3D spatial tilt card container at `/explore` using CSS 3D perspective transforms (`perspective: 1000px`, `transform-style: preserve-3d`), interactive rotation on hover, and depth elevation shadows."*

---

## 🤖 Automatic Context Schema Generation

When you invoke this skill via natural language prompts, the AI agent automatically formats the context payload:

```json
{
  "component_spec": {
    "feature_name": "<feature_name>",
    "target_route": "<target_route>",
    "rendering_mode": "rsc_with_client_boundary"
  },
  "design_system_context": {
    "aesthetic_mode": "glassmorphic",
    "token_source": "styles/globals.css"
  }
}
```

---

## 🧪 Verification Commands

To verify your generated frontend components and UI seams:

```bash
# 1. Type check TypeScript components
npx tsc --noEmit

# 2. Run code linter
npm run lint

# 3. Run unit / component tests
npm run test

# 4. Run Playwright E2E browser seam assertions
npx playwright test
```
