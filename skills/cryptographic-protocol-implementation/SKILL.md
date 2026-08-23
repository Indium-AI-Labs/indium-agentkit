---
name: cryptographic-protocol-implementation
description: Implement modern authenticated encryption, secure key exchange, mTLS, and post-quantum cryptographic primitives.
---

# Cryptographic Protocol Implementation

Implement modern, constant-time cryptographic protocols including Authenticated Encryption with Associated Data (AEAD: ChaCha20-Poly1305, AES-256-GCM), secure key exchange (X25519, Ephemeral ECDH), digital signatures (Ed25519), Mutual TLS (mTLS 1.3), key derivation (HKDF, Argon2id), and Post-Quantum Cryptography (PQC: ML-KEM / Kyber-768).

The skill is **constant-time and contract-first**: cipher suites, key entropy, nonce uniqueness, MAC tag verification, and secret memory zeroization are enforced before writing implementation code.

---

## 1. Required I/O Context Schemas & Natural Language Auto-Inference

The skill supports **two invocation modes**:

1. **🤖 Orchestrator / Technical Mode (JSON Manifest)**: Pass the JSON context manifest below.
2. **💬 Non-Technical Mode (Plain English Prompts)**: If the user provides a natural language prompt (e.g. *"Implement ChaCha20-Poly1305 authenticated encryption with HKDF key derivation for sensitive payload storage"*), the agent **must automatically infer and populate** `primitive_type`, `cipher_suite`, `secret_management`, and `compliance_standard` from the user's text and target programming language.

### JSON Context Manifest Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CryptoProtocolContextManifest",
  "type": "object",
  "required": ["protocol_spec", "security_context"],
  "properties": {
    "protocol_spec": {
      "type": "object",
      "required": ["primitive_type", "cipher_suite"],
      "properties": {
        "primitive_type": { 
          "type": "string", 
          "enum": ["aead_encryption", "key_exchange", "digital_signature", "mtls_transport", "key_derivation", "pqc_hybrid"] 
        },
        "cipher_suite": { 
          "type": "string", 
          "enum": ["chacha20_poly1305", "aes_256_gcm", "x25519_hkdf", "ed25519", "argon2id", "ml_kem_768"] 
        },
        "key_size_bits": { "type": "integer", "default": 256 },
        "nonce_size_bytes": { "type": "integer", "default": 12 }
      }
    },
    "security_context": {
      "type": "object",
      "required": ["csprng_source", "zeroize_on_free"],
      "properties": {
        "csprng_source": { "type": "string", "enum": ["web_crypto", "sys_urandom", "ring_crypto", "openssl_3"] },
        "zeroize_on_free": { "type": "boolean", "default": true },
        "constant_time_required": { "type": "boolean", "default": true }
      }
    },
    "compliance_standard": {
      "type": "object",
      "properties": {
        "standard": { "type": "string", "enum": ["rfc_8439", "fips_140_3", "cnsa_2_0", "nist_pqc"] }
      }
    }
  }
}
```

### Automatic Natural Language Inference & Weak Cipher Rejection

If no raw JSON payload is provided, apply these defaults and strict rejection checks:

- **Deprecated / Weak Cipher Rejection**: If prompt requests `RC4`, `3DES`, `MD5`, `SHA-1`, `ECB_mode`, `RSA-1024`, or plain `Diffie-Hellman`, **ABORT execution immediately** and reject with `WEAK_CIPHER_FORBIDDEN`.
- **`primitive_type`**: Inferred from requirement ("encrypt payload" $\rightarrow$ `aead_encryption`, "secure channel" $\rightarrow$ `mtls_transport`, "hash password" $\rightarrow$ `key_derivation`).
- **`cipher_suite`**: Defaults to `chacha20_poly1305` or `aes_256_gcm` for symmetric AEAD; `x25519_hkdf` for key exchange; `argon2id` for password hashing.
- **`csprng_source`**: Uses the target language's native cryptographically secure random number generator (`crypto.getRandomValues()` in JS/TS, `crypto/rand` in Go, `getrandom` / `ring` in Rust).

---

## 2. Deterministic State Machine Execution Flow

Follow this exact sequential protocol. Do not skip steps or alter execution ordering.

### Step 1: Context Ingestion & Cipher Suite Approval

1. Inspect `package.json`, `Cargo.toml`, `go.mod`, or Python dependencies.
2. Confirm libraries use audited, constant-time cryptographic primitives (Web Crypto API, `libsodium`, `ring` in Rust, `crypto/cipher` in Go, `cryptography` in Python).
3. Ensure no custom or unvetted cryptographic algorithms are created ("Never write your own crypto").

### Step 2: Key Derivation & CSPRNG Initialization

1. Use HKDF (`RFC 5869`) with SHA-256 / SHA-512 to derive sub-keys from master secrets or shared Diffie-Hellman secrets.
2. For password storage or password-based key derivation, enforce **Argon2id** ($m=65536 \text{ KB}, t=3, p=4$).
3. Generate nonces / IVs using CSPRNG sources only.

### Step 3: AEAD Authenticated Encryption Implementation

1. **Unique Nonce Guarantee**: For every encryption operation, generate a fresh, random 96-bit (12-byte) nonce. **NEVER reuse a nonce under the same key**.
2. **Associated Data (AAD) Integration**: Bind contextual metadata (user IDs, timestamps, protocol headers) as Associated Authenticated Data to prevent cipher-text substitution attacks.
3. **Tag Verification First**: Always verify the authentication tag (128-bit MAC) before releasing decrypted plaintext buffers.

### Step 4: mTLS 1.3 & Transport Security Implementation

1. Enforce TLS 1.3 (`TLS_AES_256_GCM_SHA384` or `TLS_CHACHA20_POLY1305_SHA256`). Disable SSLv3, TLS 1.0, and TLS 1.1.
2. Configure Mutual TLS (mTLS): Require client certificate verification (`ClientAuth: RequireAndVerifyClientCert`).
3. Enforce Subject Alternative Name (SAN) hostname validation and certificate pinning where applicable.

### Step 5: Memory Zeroization & Cleanup

1. Explicitly overwrite secret key buffers with zeros immediately after usage (`sodium_memzero()`, `explicit_bzero()`, or Rust `Zeroize` trait).

---

## 3. Reference Implementation: ChaCha20-Poly1305 AEAD with HKDF

```typescript
import { webcrypto } from 'node:crypto';

const crypto = webcrypto as unknown as Crypto;

// 1. HKDF Key Derivation (RFC 5869)
export async function deriveAEADKey(
  masterSecret: Uint8Array,
  salt: Uint8Array,
  info: string
): Promise<CryptoKey> {
  const masterKey = await crypto.subtle.importKey(
    'raw',
    masterSecret,
    { name: 'HKDF' },
    false,
    ['deriveKey']
  );

  return crypto.subtle.deriveKey(
    {
      name: 'HKDF',
      hash: 'SHA-256',
      salt,
      info: new TextEncoder().encode(info),
    },
    masterKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

// 2. AEAD Authenticated Encryption (AES-256-GCM / ChaCha20-Poly1305)
export interface EncryptedPayload {
  nonce: Uint8Array; // 12 Bytes (96 Bits)
  ciphertext: Uint8Array; // Payload + 16-byte MAC Tag
}

export async function encryptAEAD(
  plaintext: Uint8Array,
  key: CryptoKey,
  associatedData: Uint8Array
): Promise<EncryptedPayload> {
  // Generate fresh 96-bit CSPRNG nonce for every single operation
  const nonce = crypto.getRandomValues(new Uint8Array(12));

  const encryptedBuffer = await crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: nonce,
      additionalData: associatedData,
      tagLength: 128, // 16-byte MAC Tag
    },
    key,
    plaintext
  );

  return {
    nonce,
    ciphertext: new Uint8Array(encryptedBuffer),
  };
}

// 3. AEAD Authenticated Decryption with Tag Verification
export async function decryptAEAD(
  payload: EncryptedPayload,
  key: CryptoKey,
  associatedData: Uint8Array
): Promise<Uint8Array> {
  try {
    const decryptedBuffer = await crypto.subtle.decrypt(
      {
        name: 'AES-GCM',
        iv: payload.nonce,
        additionalData: associatedData,
        tagLength: 128,
      },
      key,
      payload.ciphertext
    );
    return new Uint8Array(decryptedBuffer);
  } catch (error) {
    // Tag verification failure or tampered ciphertext
    throw new Error('CRYPTOGRAPHIC_AUTHENTICATION_FAILED: Invalid MAC tag or tampered associated data.');
  }
}

// 4. Constant-Time Memory Zeroization
export function zeroizeBuffer(buffer: Uint8Array): void {
  buffer.fill(0);
}
```

---

## 4. Mathematical Security & Nonce Uniqueness Invariants

$$\text{AEAD Nonce Uniqueness Theorem: } \forall i \neq j, \quad Nonce_i \neq Nonce_j \quad (\text{under same } Key_k)$$

$$\text{Constant-Time Verification: } \text{Time}(\text{Compare}(A, B)) = C \quad (\text{independent of matching prefix length})$$

$$\text{Minimum Key Entropy: } H(Key) \ge 256 \text{ bits}$$

$$\text{AEAD Integrity Guardrail: } \text{Decrypt}(C, K, AAD) = \begin{cases} P, & \text{if } \text{VerifyMAC}(C, K, AAD) = \text{VALID} \\ \mathbf{ERROR}, & \text{if } \text{VerifyMAC}(C, K, AAD) = \text{INVALID} \end{cases}$$

---

## 5. Guardrails

### Operational Restrictions

- **No Homebrew Cryptography**: Never design custom encryption, hashing, or key exchange algorithms; use audited, standard implementations (`libsodium`, `Web Crypto`, `ring`).
- **No ECB Mode**: Electronic Codebook (ECB) mode is strictly forbidden. Always use AEAD modes (`AES-256-GCM`, `ChaCha20-Poly1305`).
- **No Nonce Reuse**: Reusing a nonce with GCM or Poly1305 completely breaks message integrity and leaks key material.
- **Zero Hardcoded Keys**: Secrets must never be stored in source code; load keys from secure key vaults (KMS, Vault) or environment variables.

### Security Invariants

- **Constant-Time Comparison**: Use `crypto.timingSafeEqual()` or equivalent constant-time comparison functions for secret hashes and signatures.
- **Immediate Memory Zeroization**: Overwrite secret keys in memory (`zeroize()`) as soon as cryptographic operations complete.

---

## 6. Atomic Failure Recovery & Rollback Handler

Before implementing cryptographic modules, record git baseline state. If unit tests or Wycheproof test vector validation fails:

```bash
# Revert modified files
if [ -n "${MODIFIED_FILES:-}" ]; then
  git checkout -- ${MODIFIED_FILES} 2>/dev/null
fi

# Remove newly created files
if [ -n "${CREATED_FILES:-}" ]; then
  rm -rf ${CREATED_FILES} 2>/dev/null
fi
```

---

## 7. Verification Plan & Toolchain Commands

Execute test suites and vector validation:

```bash
# 1. Run unit tests with crypto vector assertions
npm test

# 2. Run Wycheproof test vector checks (Go / Rust / Python)
go test -v ./crypto/... -run TestWycheproof
```

---

## 8. Completion Report

Report primitive types implemented, key sizes, CSPRNG sources, nonce generation strategy, AAD metadata integration, constant-time comparison verification, memory zeroization status, and test vector validation proofs.
