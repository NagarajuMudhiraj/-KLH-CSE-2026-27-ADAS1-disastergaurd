# Security Policy

## Supported Versions

We release security patches and updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## 🛡️ Defensive Security Posture

DisasterShield ADAS implements an audited **9.5 / 10** defensive security posture:
- **Zero Default Passwords & Secrets**: Dynamic environment variable enforcement with runtime secret validation.
- **Cryptographic Password Hashing**: Adaptive Bcrypt algorithm (`rounds >= 12`) with automatic legacy salt migration.
- **Role-Based Access Control (RBAC)**: Strict separation between Driver, Emergency Admin, and System telemetry roles.
- **Token Security**: Stateless PyJWT with algorithm pinning (`HS256`), short lifetimes, and token revocation.
- **Safe ML Deserialization**: Restricted weights parsing to prevent arbitrary code execution during model loading.
- **Network Resilience**: In-memory mock database fallbacks to maintain local vehicle navigation during cellular dropouts.

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability or exploit within DisasterShield ADAS, please **do not** open a public issue.

Instead, report it responsibly via:
- **GitHub Private Vulnerability Reporting**: [Report Security Advisory](https://github.com/NagarajuMudhiraj/-KLH-CSE-2026-27-ADAS1-disastergaurd/security/advisories/new)
- **Maintainer**: Direct communication through your GitHub account security portal.

Please include:
1. Description of the vulnerability and attack vector.
2. Steps or proof-of-concept to reproduce the behavior.
3. Potential impact on vehicle telemetry or navigation safety.

We will acknowledge receipt within **48 hours** and provide a patch timeline.
