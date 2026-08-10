---
name: mobile-release-safety
description: "Plan and audit mobile application releases (iOS/Android/React Native/Flutter) covering app store submission requirements, code signing, feature flags, OTA updates, and crash reporting."
---

# Mobile release safety

Plan, verify, and execute mobile application build and release workflows for iOS App Store
and Google Play Store deployments across native (Swift/Kotlin) and cross-platform (React Native/Flutter)
frameworks.

## Workflow

1. Read `AGENTS.md`, app build configuration (podfiles, build.gradle, project.pbxproj), release
   target versions, and target app stores.
2. Verify release build configuration: build numbers, bundle identifiers, min SDK/iOS deployment
   targets, and release signing certificates/keystores without exposing secrets.
3. Audit application permissions (Info.plist, AndroidManifest.xml): ensure requested permissions
   (camera, location, contacts, tracking) are justified and compliant with Apple App Store and Google Play policy.
4. Verify crash reporting and telemetry integration (Sentry, Crashlytics): ensure dSYMs / ProGuard mapping
   files are generated and uploaded for symbolication.
5. Plan Over-The-Air (OTA) JavaScript/Dart update paths (EAS Update, CodePush) if applicable, including
   channel targeting and immediate rollback conditions.
6. Verify feature flag states for new mobile features to enable remote kill-switches in case of unexpected
   device-specific crashes.
7. Conduct pre-submission verification checklist: deep links, offline caching behavior, push notification
   entitlements, and dark mode / tablet layout checks.
8. Report release readiness, store submission compliance risks, and rollback instructions.

## Guardrails

- Do not commit production keystores, certificates, private API keys, or provisioning profiles to source control.
- Ensure OTA updates comply with app store guidelines regarding dynamic code loading policies.
- An optional mobile-specialist subagent can inspect build manifests in parallel, but one agent can complete this workflow.

## Completion report

Report build numbers verified, app store compliance status, permission audit findings, symbolication mapping status,
OTA update readiness, feature flags status, and submission recommendations.
