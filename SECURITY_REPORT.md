# Application Security Assessment & Defensive Audit Report
**Project:** Disaster-Aware Intelligent Vehicle Assistance (ADAS)  
**Date:** November 2026  
**Auditor:** Senior Application Security Engineer  
**Scope:** Local codebase (`frontend/` and `backend/`), local runtime environment, static configuration, dependency manifests, and localhost API surfaces.

---

## 1. Executive Summary & Security Score

**Overall Security Score: 9.5 / 10 (Post-Remediation: LOW RISK / PRODUCTION HARDENED)**  
*(Initial Audit Baseline Score: 4.8 / 10)*

All Critical and High severity vulnerabilities identified during the defensive security audit have been successfully resolved, verified against automated test suites, and committed separately. Self-promoted administrative registration is eliminated by forcing newly registered accounts to `role="driver"`. All administrative hazard endpoints, verification queues, and disaster-zone injections are now strictly protected by a unified, reusable `require_admin` dependency. Password hashing has been migrated to `bcrypt` (cost factor 12) with automatic transparent rehashing of legacy PBKDF2 credentials, and default auto-seeded admin credentials have been replaced with environment-variable provisioning (`INITIAL_ADMIN_USERNAME` / `INITIAL_ADMIN_PASSWORD`). Fallback JWT secrets are removed with fail-fast startup enforcement. Mapbox popups and marker labels now escape all user/external strings, and `dompurify` is upgraded to the patched release (`^3.4.17`). Insecure Python `pickle.load` deserialization has been eliminated by converting `road_model.pkl` to native XGBoost JSON format. Real-time WebSockets (`/ws/emergency`, `/ws/disasters`) require authenticated JWT handshakes, and multi-tenant data access on emergency requests and prediction history is strictly isolated. Finally, Phase 2 security hardening enforces explicit origin CORS, robust HTTP security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options), 10 MB image size caps with PIL magic-byte validation, and `slowapi` rate-limiting.

---

## 2. Project Architecture & Data Flow Map

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CLIENT / DRIVER CONSOLE                         │
│  - React 19 + Vite Frontend (Mapbox GL, Leaflet, Axios, HTML5 Canvas) │
│  - Strict HTML Sanitization & Entity Escaping via DOMPurify            │
│  - JWT Bearer Header via Axios Interceptor                             │
└──────────────────┬─────────────────────────────▲───────────────────────┘
                   │ HTTPS REST (CORS Whitelist) │ Authenticated WS (?token=JWT)
                   │ Rate-Limited Endpoints      │ (/ws/emergency, /ws/disasters)
                   ▼                             │
┌────────────────────────────────────────────────┴───────────────────────┐
│                        FASTAPI BACKEND RUNTIME                         │
│  - Security Headers: CSP, HSTS, X-Frame-Options, X-Content-Type-Options│
│  - Auth & RBAC: Bcrypt, PyJWT (Mandatory Env Secret), require_admin    │
│  - Rate Limiter: SlowAPI (Login: 10/min, Predict: 20/min)              │
│  - Input Hardening: 10MB Ceiling + PIL Magic Byte Signature Verification│
└─────────┬──────────────────────┬──────────────────────────┬────────────┘
          │                      │                          │
          ▼                      ▼                          ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────────┐
│   MONGODB / MEM  │   │    AI ENGINES    │   │   EXTERNAL TELEMETRY     │
│ - collections:   │   │ - YOLOv11s (.pt) │   │ - OpenWeatherMap API     │
│   users, hazards,│   │ - XGBoost V4 JSON│   │ - Open-Meteo Weather API │
│   emergency, etc.│   │ - XGBoost Legacy │   │ - Mapbox Vector Tiles    │
│ - Multi-tenant   │   │   JSON (No Pickle│                              │
│   isolated query │   │   Deserialization│                              │
└──────────────────┘   └──────────────────┘   └──────────────────────────┘
```

---

## 3. Comprehensive Findings & Remediation Verification Table

| ID | Severity | Category | Target Component | Description | Status | Verification & Resolution Summary |
|---|---|---|---|---|---|---|
| **SEC-01** | **CRITICAL** | Broken Access Control | [`backend/app/models/schemas.py`](file:///d:/datasets_IDM(ADAS)/backend/app/models/schemas.py), [`backend/app/api/auth.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/auth.py) | Self-assignment of administrative role during public registration. | **RESOLVED** | Removed `role` field from `UserRegister` schema. Forced `role="driver"` on database insert and token generation. Verified via `tests/test_sec01_role_escalation.py`. |
| **SEC-02** | **CRITICAL** | Broken Access Control | [`backend/app/utils/security.py`](file:///d:/datasets_IDM(ADAS)/backend/app/utils/security.py), [`backend/app/api/hazards.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/hazards.py), [`navigation.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/navigation.py) | Administrative hazard endpoints and disaster zones lacked role checks. | **RESOLVED** | Created unified `require_admin` dependency. Applied to `/admin/create`, `/admin/{id}`, `/admin/status`, `/admin/delete`, `/admin/reports`, `/admin/reports/purge`, `/verify`, `/restricted-zones`, and `POST /disaster-zones`. Verified via `tests/test_sec02_rbac.py`. |
| **SEC-03** | **CRITICAL** | Stored XSS | [`frontend/src/components/map/LiveMap.jsx`](file:///d:/datasets_IDM(ADAS)/frontend/src/components/map/LiveMap.jsx), [`AdminHazardMapView.jsx`](file:///d:/datasets_IDM(ADAS)/frontend/src/components/admin/AdminHazardMapView.jsx) | Unescaped hazard name, address, and description in Mapbox popups and markers. | **RESOLVED** | Upgraded `dompurify` to `3.4.17` (patched against GHSA advisories). Implemented `escapeHtml` utility and applied to all Mapbox popups and marker badges in both driver and admin maps. Verified via frontend build and unit test. |
| **SEC-04** | **CRITICAL** | Cryptographic Failures | [`backend/app/utils/security.py`](file:///d:/datasets_IDM(ADAS)/backend/app/utils/security.py), [`mongodb.py`](file:///d:/datasets_IDM(ADAS)/backend/app/database/mongodb.py) | Static salt in PBKDF2 hashing; default `admin/admin123` auto-seeded on boot. | **RESOLVED** | Replaced with dynamic per-user salted `bcrypt` (12 rounds). Implemented legacy PBKDF2 verifier with automatic transparent migration to bcrypt on successful login. Removed default admin seeding; initial admin credentials read from `INITIAL_ADMIN_USERNAME` / `INITIAL_ADMIN_PASSWORD`. Verified via `tests/test_sec04_bcrypt_migration.py`. |
| **SEC-05** | **HIGH** | Insecure Deserialization (CWE-502) | [`backend/app/services/ai_service.py`](file:///d:/datasets_IDM(ADAS)/backend/app/services/ai_service.py) | Use of Python `pickle.load` on `road_model.pkl` (Arbitrary RCE risk). | **RESOLVED** | Converted `road_model.pkl` to `road_model.json` using XGBoost native format. Loaded via `XGBClassifier().load_model()`. Removed `pickle.load` and `import pickle` entirely. Deleted `.pkl` files from repository. Predictions verified identical to baseline via `tests/test_sec05_model_deserialization.py`. |
| **SEC-06** | **HIGH** | Broken Authentication (WebSocket) | [`backend/app/api/emergency.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/emergency.py), [`backend/app/api/navigation.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/navigation.py) | Emergency SOS and Disaster WebSocket streams lacked handshake authentication. | **RESOLVED** | Added `token: Optional[str] = Query(None)` to `/ws/emergency` and `/ws/disasters`. Handshakes without valid JWT are immediately rejected with WS code 1008 (Policy Violation). Verified via `tests/test_sec06_sec08_ws_and_isolation.py`. |
| **SEC-07** | **HIGH** | Secrets Management | [`backend/app/utils/security.py`](file:///d:/datasets_IDM(ADAS)/backend/app/utils/security.py) | Hardcoded static fallback JWT secret key in source code. | **RESOLVED** | Removed static fallback secret string. Application throws a fatal `RuntimeError` on startup if `JWT_SECRET_KEY` is not set in the environment. Verified via `tests/test_sec07_jwt_secret.py`. |
| **SEC-08** | **HIGH** | Broken Access Control / IDOR | [`backend/app/api/emergency.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/emergency.py), [`backend/app/api/dashboard.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/dashboard.py), [`road_prediction.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/road_prediction.py) | Regular drivers could query emergency requests, prediction history, and route history for other citizens. | **RESOLVED** | Restricted `/emergency/list`, `/history`, and `/routes/history` so non-admin drivers are strictly constrained to records matching their authenticated username (`current_user["username"]`). Admin role retains system-wide visibility. Verified via `tests/test_sec06_sec08_ws_and_isolation.py`. |
| **SEC-09** | **MEDIUM** | Input Validation / DoS | [`backend/app/api/prediction.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/prediction.py) | Image uploads lacked size limits and verified only client-controlled MIME header. | **RESOLVED** | Implemented a strict 10 MB file size limit returning HTTP 413. Added PIL magic-byte signature validation (`Image.open(io.BytesIO(contents)).verify()`) to reject non-image and corrupted uploads with HTTP 400. Verified via `tests/test_phase2_security_hardening.py`. |
| **SEC-10** | **MEDIUM** | Security Misconfiguration | [`backend/app/main.py`](file:///d:/datasets_IDM(ADAS)/backend/app/main.py) | CORS configured with wildcard origin `allow_origins=["*"]` with credentials enabled. | **RESOLVED** | Restricted `allow_origins` to explicit whitelist loaded from `ALLOWED_ORIGINS` (defaults to trusted local dev origins `http://localhost:5173`, `http://localhost:3000`). Verified via `tests/test_phase2_security_hardening.py`. |
| **SEC-11** | **MEDIUM** | Security Misconfiguration | [`backend/app/main.py`](file:///d:/datasets_IDM(ADAS)/backend/app/main.py) | Missing standard security headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS). | **RESOLVED** | Added custom HTTP middleware returning `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, `Strict-Transport-Security`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Content-Security-Policy`. Verified via `tests/test_phase2_security_hardening.py`. |
| **SEC-12** | **MEDIUM** | Rate Limiting | [`backend/app/api/auth.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/auth.py), [`backend/app/api/prediction.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/prediction.py), [`road_prediction.py`](file:///d:/datasets_IDM(ADAS)/backend/app/api/road_prediction.py) | No rate-limiting protection on login or GPU/CPU-heavy vision inference endpoints. | **RESOLVED** | Integrated `slowapi` rate limiter with keying on client IP. Throttles `/auth/login` to 10/min, `/predict-image` to 20/min, and `/predict-road` to 60/min with HTTP 429 responses. Verified via `tests/test_phase2_security_hardening.py`. |
| **SEC-13** | **LOW** | Vulnerable Dependencies | [`frontend/package.json`](file:///d:/datasets_IDM(ADAS)/frontend/package.json) | Vulnerabilities in DOMPurify (`<=3.4.16`). | **RESOLVED** | Upgraded `dompurify` to `^3.4.17`. Critical GHSA advisories eliminated. |

---

## 4. Git History Audit & Key Rotation Advisory

### A. Git History Leak Audit
A search across all commits, branches, and trees was performed:
* **OpenWeather API Key (`8db4aad631e3f1bb87ecb6826cdc7c69`):** `0 commits found`. The key was never committed to git.
* **Mapbox Public Token (`pk.eyJ1IjoiZGVzdHJveWVyMzQ1...`):** `0 commits found`. The token was never committed to git.
Both secrets have only ever existed in untracked local `.env` files protected by `.gitignore`.

### B. Keys to Rotate
Even though git history is clean, the following operational rotations should be executed:
1. **Mapbox Public Token:** Mapbox public tokens are sent to client browsers by design. In the Mapbox account dashboard, add a **URL restriction** allowing only your production domain and local dev ports (`localhost:*`). If transitioning from staging/dev to production, generate a separate restricted production token.
2. **OpenWeather API Key:** If this development screen or workstation was ever shared, recorded, or demonstrated, rotate the key in your OpenWeatherMap developer dashboard and update `backend/.env`.
3. **Production JWT Secret (`JWT_SECRET_KEY`):** Ensure the production environment uses a fresh, cryptographically strong 64-character secret generated via `openssl rand -hex 32`.

---

## 5. Remaining Low / Operational Items

1. **HttpOnly Cookie Architecture (Optional Future Enhancement):**
   * *Status:* Defense-in-depth recommendation.
   * *Detail:* JWT tokens are currently stored in browser `localStorage`. Storing authentication tokens in `HttpOnly`, `SameSite=Strict`, `Secure` cookies eliminates all JavaScript access to tokens, providing defense-in-depth even if a client-side XSS were ever introduced.
2. **Production Reverse Proxy / TLS Termination:**
   * In a live cloud/server deployment, ensure TLS termination is handled by Nginx, Caddy, or Cloudflare with automated Let's Encrypt certificates to enforce HTTPS for all HTTP and WebSocket connections.

