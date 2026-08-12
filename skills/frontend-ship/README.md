# Frontend Ship Skill (`skills/frontend-ship`)

The **`frontend-ship`** skill provides AI coding agents (Claude Code, Cursor, Codex, Antigravity CLI) with deterministic, accessible, and high-performance frontend UI engineering protocols.

---

## ⚡ 1-Line Quick Installation

To install this skill into any project repository in under 2 seconds, run:

```bash
npx indium-agentkit add frontend-ship
```

*Automatically configures Cursor rules (`.cursor/rules/frontend-ship.mdc`), Claude Code (`CLAUDE.md`), and Windsurf / Copilot configurations.*

---

## 💬 Zero-JSON Non-Technical Mode (Plain English Prompts)

Non-technical users do **not** need to write or see any JSON manifests. Simply copy and type a plain English sentence into Cursor, Claude Code, or Antigravity:

### 🌟 Simple Plain English Prompt Formula
> *"Use `@frontend-ship` to design a **[aesthetic]** **[component name]** at **[route]**."*

### 💡 Examples:
- **Glassmorphism**: *"Use `@frontend-ship` to design a glassmorphic user profile card at `/settings/profile`."*
- **Minimalist**: *"Use `@frontend-ship` to design a minimalist dark-mode pricing table at `/pricing`."*
- **Expressive**: *"Use `@frontend-ship` to design an expressive analytics dashboard card at `/dashboard`."*
- **3D Spatial**: *"Use `@frontend-ship` to design a 3D spatial tilt product card at `/products`."*

The AI Agent automatically infers all routes, visual design tokens, state machine views, and accessibility rules behind the scenes!

---

## 🤖 Technical / Orchestrator Mode (JSON Manifest)

For automated pipelines or developer workflows connecting to backend endpoints:

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

## 🎭 Aesthetic Mode Options

- 💎 **`glassmorphic`**: Translucent cards, blur filters (`blur(16px)`), specular rim light borders, radial aurora glow.
- ✨ **`minimalist`**: Clean monochromatic surfaces, high contrast readability, subtle hairline borders.
- 🔥 **`expressive`**: Micro-interaction spring physics (`cubic-bezier(0.16, 1, 0.3, 1)`), hover lifts, vibrant brand accents.
- 🧊 **`spatial_3d`**: CSS 3D perspective transforms (`perspective: 1000px`, `transform-style: preserve-3d`), hover tilt cards.

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
