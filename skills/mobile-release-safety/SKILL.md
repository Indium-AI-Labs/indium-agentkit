---
name: mobile-release-safety
description: Plan and audit mobile application releases (iOS/Android/React Native/Flutter) covering app store compliance, code signing, feature flags, OTA updates, and crash symbolication.
---

# Mobile Release Safety

Plan, audit, and execute mobile application release workflows for iOS App Store Connect and Google Play Console deployments across native (Swift, Kotlin) and cross-platform (React Native, Flutter) frameworks.

The skill is **contract-first and store-compliant**: app versioning, bundle identifiers, Privacy Manifests (`PrivacyInfo.xcprivacy`), permission usage descriptions, code signing keystores, dSYM / ProGuard mapping file symbolication, Over-The-Air (OTA) JS bundles, and remote kill-switch feature flags are verified before submitting builds.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Audit our React Native app build for iOS App Store and Google Play submission including dSYM uploads, permissions, and EAS OTA updates"*), the agent **must automatically infer and populate** `platform`, `bundle_id`, `release_version`, and `ota_provider` from the user's text and repository configuration.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MobileReleaseSafetyContextManifest",
  "type": "object",
  "required": ["release_target", "build_config"],
  "properties": {
    "release_target": {
      "type": "object",
      "required": ["platform", "bundle_id"],
      "properties": {
        "platform": { 
          "type": "string", 
          "enum": ["ios", "android", "react_native", "flutter", "dual_platform"],
          "default": "dual_platform" 
        },
        "bundle_id": { "type": "string", "pattern": "^[a-zA-Z0-9_.]+$" },
        "version_name": { "type": "string", "default": "1.0.0" },
        "version_code": { "type": "integer", "default": 100 }
      }
    },
    "build_config": {
      "type": "object",
      "required": ["signing_environment"],
      "properties": {
        "signing_environment": { 
          "type": "string", 
          "enum": ["fastlane_match", "app_store_connect_api", "play_custom_keystore"],
          "default": "fastlane_match" 
        },
        "symbolication_upload_enabled": { "type": "boolean", "default": true },
        "min_ios_version": { "type": "string", "default": "15.0" },
        "min_android_sdk": { "type": "integer", "default": 24 }
      }
    },
    "ota_and_flags": {
      "type": "object",
      "properties": {
        "ota_provider": { "type": "string", "enum": ["eas_update", "codepush", "none"], "default": "none" },
        "remote_kill_switch_enabled": { "type": "boolean", "default": true }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Store Safety Rules

If no raw JSON payload is provided, apply these defaults and strict app store safety rules:

- **Zero Secret Commits**: NEVER commit `.keystore`, `.jks`, `.p12`, `.mobileprovision`, or service account JSON files to source control.
- **Privacy Manifest Verification**: iOS builds targeting iOS 17+ MUST include valid `PrivacyInfo.xcprivacy` declaring Required Reason APIs (system boot time, user defaults, disk space).
- **ProGuard / dSYM Upload**: Release builds MUST generate and upload mapping files (ProGuard `mapping.txt` or Xcode dSYMs) to Sentry / Firebase Crashlytics for symbolication.

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Build Manifest & Version Code Audit

1. Inspect project manifests:
   - iOS: `Info.plist`, `project.pbxproj` (`CFBundleShortVersionString`, `CFBundleVersion`).
   - Android: `app/build.gradle` (`versionName`, `versionCode`).
   - Flutter: `pubspec.yaml` (`version: 1.0.0+100`).
2. Verify version code auto-increment: `versionCode` must strictly increase over previous store submissions.

### Step 2: Permission Justification & Privacy Manifest Check

1. Audit requested permissions:
   - iOS `Info.plist`: Ensure every requested permission (`NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription`, `NSUserTrackingUsageDescription`) has a clear, non-generic user explanation.
   - Android `AndroidManifest.xml`: Verify dangerous permissions (`CAMERA`, `ACCESS_FINE_LOCATION`, `POST_NOTIFICATIONS`) match Google Play Store declared policies.
2. Verify Apple Privacy Manifest (`PrivacyInfo.xcprivacy`) declarations for third-party SDK tracking.

### Step 3: Code Signing & Symbolication Mapping Upload

1. Verify release code signing certificates using Fastlane Match or Xcode / Gradle release configurations.
2. Ensure dSYMs (iOS) and ProGuard `mapping.txt` (Android) are automatically uploaded to Sentry or Firebase Crashlytics in the release pipeline.

### Step 4: Over-The-Air (OTA) Updates & Kill Switches

1. Verify OTA update channels (EAS Update, CodePush):
   - Enforce runtime JS bundle runtime version matching (`runtimeVersion` in Expo).
   - Ensure dynamic code loading complies with Apple App Store Review Guideline 2.5.2 (no functional feature changes via OTA).
2. Configure remote feature flag kill-switches (Firebase Remote Config, LaunchDarkly) for instant feature rollback without re-submitting builds.

### Step 5: Pre-Submission Verification Suite

1. Check deep linking (`URL Schemes`, `Universal Links` / `App Links` via `apple-app-site-association` and `.well-known/assetlinks.json`).
2. Verify offline caching state and dark mode / tablet layout rendering.

---

## 3. Reference Implementation: Node.js / Fastlane Mobile Release Validator

```javascript
import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';

export interface MobileReleaseAuditReport {
  platform: 'ios' | 'android' | 'cross_platform';
  passed: boolean;
  checks: Array<{ name: string; status: 'PASS' | 'FAIL' | 'WARN'; message: string }>;
}

export function auditMobileRelease(projectRoot: string): MobileReleaseAuditReport {
  const report: MobileReleaseAuditReport = {
    platform: 'cross_platform',
    passed: true,
    checks: [],
  };

  // 1. Check iOS Privacy Manifest (PrivacyInfo.xcprivacy)
  const privacyManifestPath = resolve(projectRoot, 'ios/PrivacyInfo.xcprivacy');
  if (existsSync(privacyManifestPath)) {
    report.checks.push({ name: 'iOS Privacy Manifest', status: 'PASS', message: 'PrivacyInfo.xcprivacy found.' });
  } else {
    report.checks.push({
      name: 'iOS Privacy Manifest',
      status: 'WARN',
      message: 'PrivacyInfo.xcprivacy missing. Required for iOS 17+ App Store submissions.',
    });
  }

  // 2. Check Android ProGuard / R8 Mapping File Config
  const gradlePath = resolve(projectRoot, 'android/app/build.gradle');
  if (existsSync(gradlePath)) {
    const gradleContent = readFileSync(gradlePath, 'utf-8');
    if (gradleContent.includes('minifyEnabled true')) {
      report.checks.push({ name: 'Android ProGuard Minification', status: 'PASS', message: 'Minification and mapping generation enabled.' });
    } else {
      report.checks.push({ name: 'Android ProGuard Minification', status: 'WARN', message: 'minifyEnabled is set to false in release build.' });
    }
  }

  // 3. Check for Secret Keystore Leaks in Git
  const gitignorePath = resolve(projectRoot, '.gitignore');
  if (existsSync(gitignorePath)) {
    const gitignore = readFileSync(gitignorePath, 'utf-8');
    if (gitignore.includes('*.keystore') || gitignore.includes('*.jks')) {
      report.checks.push({ name: 'Keystore Git Isolation', status: 'PASS', message: 'Android keystores excluded in .gitignore.' });
    } else {
      report.passed = false;
      report.checks.push({ name: 'Keystore Git Isolation', status: 'FAIL', message: 'CRITICAL: *.keystore / *.jks not found in .gitignore!' });
    }
  }

  return report;
}

if (require.main === module) {
  const rep = auditMobileRelease(process.cwd());
  console.log(JSON.stringify(rep, null, 2));
}
```

---

## 4. Mobile Release Invariants & SLA Metrics

$$\text{Crash-Free Sessions Target: } \text{CrashFreeRate} \ge 99.9\%$$

$$\text{App Binary Size Growth: } \frac{\text{Size}_{\text{new}} - \text{Size}_{\text{old}}}{\text{Size}_{\text{old}}} \times 100\% \le 10\%$$

$$\text{Cold Start SLA: } t_{\text{cold\_start}} \le 1.5\text{ seconds}$$

$$\text{OTA JS Bundle Guideline (Apple 2.5.2): } \text{Scope}(\text{OTA}) \equiv \text{Bug Fixes} \quad (\text{No major structural changes})$$

---

## 5. Guardrails

### Operational Restrictions

- **Zero Secret Commits**: Keystores (`.jks`), P12 certificates, and API key JSON files MUST NOT be committed to git.
- **Strict OTA Scoping**: OTA updates (EAS Update, CodePush) must only be used for JS bug fixes, never for injecting new un-reviewed native features.
- **Mandatory Rollback Kill-Switches**: All new major mobile features must be wrapped in Remote Config feature flags for instant emergency disabling.

---

## 6. Atomic Failure Recovery & Rollback Handler

If a deployed mobile build produces unexpected crash spikes in production:

```bash
# 1. Trigger immediate OTA JS Rollback (if applicable)
eas update:rollback --channel production 2>/dev/null

# 2. Toggle Remote Config Feature Flag Kill-Switch
python3 scripts/toggle_feature_flag.py --flag new_checkout_flow --state false
```

---

## 7. Verification Plan & Toolchain Commands

Execute mobile release pre-submission checks:

```bash
# 1. Run Fastlane release precheck for iOS and Android
fastlane run precheck

# 2. Run mobile release safety auditor script
node scripts/audit_mobile_release.js

# 3. Verify Expo / React Native OTA update compatibility
npx eas-cli update:configure
```

---

## 8. Completion Report

Report target platforms (iOS, Android), version name and version code verified, Privacy Manifest compliance, permission justifications audited, dSYM / ProGuard mapping file symbolication status, OTA update channels configured, remote kill-switch feature flags verified, and final app store submission readiness verdict.
