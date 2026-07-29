# bOPEN Programming Language Stacks Matrix & Scoring Measure Specification v1.0

**Document ID:** `BOPEN-ENG-LANG-001`  
**Version:** `1.0`  
**Status:** Approved Specification  
**Issued:** 2026-07-29  
**Owner:** Engineering Authority & Architecture Authority  
**Classification:** Quantitative Language Stack Evaluation & Engineering Baseline  

---

## 1. Weighted Evaluation Criteria

Programming language runtimes for bOPEN kernel modules, services, SDKs, and deployment stamps are evaluated on a 1.0 to 10.0 scale across 6 weighted dimensions:

$$\text{Final Score} = 0.20 \cdot \text{TYPE} + 0.20 \cdot \text{PERF} + 0.20 \cdot \text{AGENT} + 0.15 \cdot \text{ISO} + 0.15 \cdot \text{DEV} + 0.10 \cdot \text{ECO}$$

| Abbr | Evaluation Dimension | Weight | Description |
| :--- | :--- | :---: | :--- |
| **TYPE** | Type Safety & Contract Verification | **20%** | Strict static/gradual typing, JSON schema validation, interface clarity. |
| **PERF** | Execution Performance & Concurrency | **20%** | P99 latency, memory footprint, async I/O concurrency efficiency. |
| **AGENT** | AI Agent & Multi-LLM Tooling Compatibility | **20%** | Ease of generation/refactoring by AI agents (Gemini, Claude, Codex, Kimi). |
| **ISO** | Multi-Tenant Context Safety | **15%** | Async context propagation (`AsyncLocalStorage`/`ContextVar`), thread safety. |
| **DEV** | Developer Velocity & Ergonomics | **15%** | Ecosystem tooling, fast testing, package management (`pnpm`, `uv`). |
| **ECO** | Enterprise Adoption & License | **10%** | Community support, OSS library maturity, permissive licensing. |

---

## 2. Programming Language Evaluation Matrix

| Language Runtime | TYPE (20%) | PERF (20%) | AGENT (20%) | ISO (15%) | DEV (15%) | ECO (10%) | Final Weighted Score | Assigned bOPEN Role & Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **TypeScript / Node.js (v20+)** | **9.5** | **8.5** | **9.5** | **9.0** | **9.5** | **9.5** | **9.25 / 10** | **PRIMARY** (API Gateway, Client SDKs, Web Apps) |
| **Python (3.12+)** | **8.5** | **7.5** | **10.0** | **9.0** | **9.5** | **9.5** | **8.90 / 10** | **PRIMARY** (Kernel Core, AI Agent Layer, Data Services) |
| **Go (Golang 1.22+)** | **9.0** | **9.5** | **8.5** | **9.0** | **8.5** | **9.0** | **8.95 / 10** | **TARGET** (High-Throughput Microservice Deployment Stamps) |
| **Rust (1.75+)** | 10.0 | 10.0 | 7.5 | 9.0 | 7.0 | 8.0 | **8.60 / 10** | **SPECIALTY** (Wasm Policy Plugins & Cryptographic Modules) |
| **Java 21 / Kotlin** | 9.0 | 8.5 | 8.0 | 8.5 | 7.5 | 8.5 | **8.35 / 10** | REJECTED FOR KERNEL (Heavy Memory Footprint) |
| **C# / .NET 8** | 9.0 | 8.5 | 8.0 | 8.5 | 8.0 | 8.0 | **8.35 / 10** | REJECTED FOR KERNEL (Enterprise Overhead) |

---

## 3. Framework Selection & Architecture Baseline

### 3.1 TypeScript Stack Baseline
* **Runtime**: Node.js v20+ / Bun
* **Web Framework**: Hono / Express (Fast async routing)
* **Contract Schema**: `zod` / `typebox` (Bi-directional JSON Schema generation matching `contracts/schemas/`)
* **Context Propagation**: Node.js `AsyncLocalStorage` for `X-Tenant-ID` context binding.

### 3.2 Python Stack Baseline
* **Runtime**: Python 3.12+ (using `uv` package manager)
* **Web Framework**: FastAPI (Asynchronous ASGI)
* **Contract Schema**: Pydantic v2 (Native Rust-backed JSON schema validation matching `contracts/schemas/`)
* **Context Propagation**: `contextvars.ContextVar` for thread-safe `tenant_id` context binding.

### 3.3 Go Stack Baseline
* **Runtime**: Go 1.22+
* **Web Framework**: Gin / Fiber
* **Context Propagation**: `context.Context` explicit propagation per method call.

---

## 4. Operational Invariants

1. **No Untyped Any / Dynamic Bypasses**: All TypeScript must enforce `strict: true`. All Python must use explicit type annotations (`mypy` compliant).
2. **Context Leakage Prevention**: Thread-local / async local context MUST be explicitly cleared upon request completion.
3. **Threshold Gate**: Runtimes scoring below **8.5 / 10** are prohibited for core bOPEN platform kernel implementation.
