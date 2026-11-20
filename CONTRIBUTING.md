# Contributing to DisasterShield ADAS

Thank you for your interest in contributing to **DisasterShield ADAS**! We welcome contributions from developers, researchers, roboticists, and disaster response specialists worldwide.

---

## 🛠️ Getting Started

### 1. Prerequisites
- **Python**: 3.11 or 3.12
- **Node.js**: 20+ (with npm or yarn)
- **Git**

### 2. Fork and Clone
```bash
git clone https://github.com/<your-username>/-KLH-CSE-2026-27-ADAS1-disastergaurd.git
cd -KLH-CSE-2026-27-ADAS1-disastergaurd
```

### 3. Quick Verification
Verify that the core algorithm pipeline runs cleanly on your machine before making changes:
```bash
python core_pipeline_snippets.py
```
Expected output: All 3 core algorithm suites validated in sub-2 seconds with zero external server dependencies.

---

## 🌿 Branching Strategy

- `main`: Production-ready, audited releases.
- Feature branches: `feat/<feature-name>` (e.g., `feat/lidar-hazard-fusion`)
- Fix branches: `fix/<bug-name>` (e.g., `fix/hann-window-boundary`)

---

## 📋 Code Standards

- **Python**: Follow PEP 8 guidelines. Type hints are strongly encouraged.
- **Frontend**: Clean functional React 19 components with structured props.
- **Safety**: Do not introduce unvetted third-party dependencies into the sub-25ms pathfinding loop.
- **Documentation**: Update the corresponding documentation in `docs/` and `README.md` if your PR modifies algorithms, contracts, or schemas.

---

## 🚀 Submitting a Pull Request

1. Push your changes to your feature branch.
2. Ensure `python core_pipeline_snippets.py` runs without regressions.
3. Open a Pull Request against the `main` branch.
4. Fill in the provided [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).
5. A maintainer will review your code and CI checks will run automatically.

---

## 💬 Community & Questions

Feel free to open an **Issue** for discussions, feature requests, or algorithm improvements!
