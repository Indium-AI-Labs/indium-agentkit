# Frontend Ship Skill (`skills/frontend-ship`)

The **`frontend-ship`** skill provides AI coding agents (Claude Code, Cursor, Codex, Antigravity CLI) with deterministic, accessible, and high-performance frontend UI engineering protocols.

---

## ⚡ Setup Guide: Terminal & Web UI

### Option A: Terminal & Local AI Editors (Cursor, Claude Code, Windsurf)
Run this single command in your project terminal:

```bash
npx github:sagarrathi16/indium-agentkit add frontend-ship
```
*Automatically configures Cursor rules (`.cursor/rules/frontend-ship.mdc`), Claude Code (`CLAUDE.md`), and Windsurf / Copilot configurations directly from GitHub!*

---

### Option B: Web Chat UIs (Claude.ai, ChatGPT, Claude Projects, Custom GPTs)

#### 1. Claude.ai Projects / ChatGPT Custom GPTs (Recommended — Set Once, Use Forever)
1. Open your **Claude Project** or **Custom GPT**.
2. Click **"Add Knowledge"** / **"Project Knowledge"**.
3. Upload [SKILL.md](SKILL.md) or copy-paste its raw text.
4. Now simply type plain English prompts in your chat session!

#### 2. One-Shot Web Chat (Claude.ai / ChatGPT / Gemini Web)
Paste `SKILL.md` into your chat opening:
> *"Adopt this skill protocol: **[Paste SKILL.md content]**. Now build a glassmorphic user profile card at `/profile`."*

---

## 💬 Zero-JSON Non-Technical Mode (Plain English Prompts)

Non-technical users do **not** need to write or see any JSON manifests. Simply copy and type a plain English sentence:

### 🌟 Simple Plain English Prompt Formula
> *"Use `@frontend-ship` to design a **[aesthetic]** **[component name]** at **[route]**."*

### 💡 Examples:
- **Glassmorphism**: *"Use `@frontend-ship` to design a glassmorphic user profile card at `/settings/profile`."*
- **Minimalist**: *"Use `@frontend-ship` to design a minimalist dark-mode pricing table at `/pricing`."*
- **Expressive**: *"Use `@frontend-ship` to design an expressive analytics dashboard card at `/dashboard`."*
- **3D Spatial**: *"Use `@frontend-ship` to design a 3D spatial tilt product card at `/products`."*

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

To verify generated frontend components and UI seams:

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
