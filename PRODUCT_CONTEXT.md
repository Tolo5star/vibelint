# VIBELINT — Product Context Document

> **Open-source AI code pattern scanner. Catch the bugs AI writes 2.74x more often.**
> Research-backed rules. Multi-language. CLI-first.

---

## Problem Statement

AI-generated code has a specific, documented failure profile. It's not "bad code" in general — it fails in predictable, research-backed patterns that existing linters don't catch. AI code has 1.7x more issues, 2.74x more XSS vulnerabilities, 1.88x more hardcoded secrets, and 1.75x more logic errors than human-written code. 66% of developers spend more time fixing "almost-right" AI code than writing it from scratch.

Existing tools either detect IF code is AI-generated (SonarQube AI Code Assurance) or apply generic security scanning (Semgrep, Snyk). Nobody has built a scanner specifically targeting the documented failure patterns that AI generators consistently produce.

**VibeLint is the ESLint for the AI coding era.** Research-backed rules targeting the specific patterns AI gets wrong, across languages.

---

## What VibeLint Is NOT

- Not a generic linter (ESLint, Pylint do that)
- Not a SAST security scanner (Semgrep, Snyk do that)
- Not an AI code detector (SonarQube does that)
- Not a code review bot (CodeRabbit, Qodo do that)

## What VibeLint IS

A scanner that knows HOW AI fails and catches those specific patterns. Each rule cites the research, shows the failure multiplier, and provides the fix.

---

## Competitive Landscape (April 2026)

| Tool | What It Does | Why It's Not VibeLint |
|---|---|---|
| SonarQube AI Code Assurance | Detects IF code is AI-generated, applies standard rules harder | Doesn't have AI-FAILURE-PATTERN-specific rules |
| Semgrep Multimodal | AI + rule-based security analysis, 8x fewer false positives | Security-focused, not AI-pattern-specific |
| CodeRabbit | AI code review on PRs ($24/mo/dev). 13M PRs reviewed | Reviews all code, not AI-specific pattern detection |
| VibeFix | GitHub bot. AI density scoring, VibeScore rankings | Commercial, not OSS, PR-workflow only |
| VibeCheck | 150+ secret patterns for vibe-coded apps | Security scanning only. $5-29/mo |
| Aikido | Full AppSec (SAST+DAST+SCA+secrets) | Generic AppSec, not AI-pattern-aware |
| eslint-plugin-llm-core | 20 ESLint rules for AI coding mistakes | JS/TS only, one developer, 20 rules |
| eslint-for-ai | ESLint rules for AI generator mistakes | JS/TS only, tiny project |

**The gap:** No OSS, multi-language, research-backed scanner targeting specific AI failure patterns.

---

## Research Foundation

### Key Studies

| Study | Finding |
|---|---|
| CodeRabbit Report (Dec 2025) | AI code: 1.7x more issues, 1.75x logic errors, 1.64x maintainability issues, 1.57x security findings |
| Carnegie Mellon Benchmark | 61% passed functional tests, only 10.5% passed security tests |
| Survey of Bugs in AI-Generated Code (Dec 2025) | Semantic errors = 60%+ of all faults |
| AI Vyuh Report | 53% of AI-generated code ships with vulnerabilities |
| Technical Debt Study | AI tech debt grew from hundreds to 110,000+ issues in one year |

### Specific Failure Multipliers

| Pattern | AI vs Human Multiplier |
|---|---|
| XSS vulnerabilities | 2.74x more likely |
| Insecure object references | 1.91x |
| Improper password handling | 1.88x |
| Insecure deserialization | 1.82x |
| Logic / correctness errors | 1.75x |
| Code quality / maintainability | 1.64x |
| Security findings (general) | 1.57x |
| Performance issues | 1.42x |

---

## V1 Scope

### Starting Rule Set (15 rules, research-backed)

**Security Rules:**
| ID | Pattern | Source |
|---|---|---|
| AI-SEC-001 | Hardcoded secrets disguised as placeholders (`sk-placeholder-xxx`) | 1.88x multiplier |
| AI-SEC-002 | XSS via unsanitized user input (dangerouslySetInnerHTML, f-strings in HTML) | 2.74x multiplier |
| AI-SEC-003 | Insecure direct object references (missing auth checks on resource access) | 1.91x multiplier |
| AI-SEC-004 | Over-permissive CORS defaults (`*` origin) | 53% ship vulnerable |
| AI-SEC-005 | Missing auth middleware on route handlers | CMU: 10.5% pass security |

**Logic Rules:**
| ID | Pattern | Source |
|---|---|---|
| AI-LOGIC-001 | Async function in array methods (.map/.filter returns Promise[]) | eslint-plugin-llm-core |
| AI-LOGIC-002 | Catch-all error handling (swallows errors silently) | 60% semantic errors |
| AI-LOGIC-003 | Off-by-one in pagination/slicing | 1.75x logic errors |
| AI-LOGIC-004 | Missing null/undefined checks on optional chains | Empirical study |
| AI-LOGIC-005 | Incorrect boolean logic in compound conditions | Semantic error taxonomy |

**Quality Rules:**
| ID | Pattern | Source |
|---|---|---|
| AI-QUAL-001 | `any` type when specific type is inferrable (TypeScript) | Common AI anti-pattern |
| AI-QUAL-002 | Redundant/contradictory comments vs code | AI pattern documentation |
| AI-QUAL-003 | Unused imports/variables from incomplete refactors | 1.64x maintainability |
| AI-QUAL-004 | Dead code paths from partial edits | Tech debt study |
| AI-QUAL-005 | Magic numbers without named constants | AI anti-pattern |

### Each Rule Includes
- Pattern it detects (with AST matching or regex)
- Research citation and failure multiplier
- Auto-fix suggestion
- Code examples (bad + good)

### Languages (V1)
- JavaScript / TypeScript
- Python
- (Go, Rust, Java in v0.2+)

### Delivery
- CLI: `vibelint scan ./src`
- Output formats: terminal (default), JSON, SARIF (for GitHub Code Scanning)
- CI/CD: GitHub Action, GitLab CI template
- Config: `.vibelint.yaml` for rule customization
- Exit codes: configurable fail threshold (e.g., fail on critical only)

---

## Target Developer Experience

```bash
# Install
pip install vibelint
# or
npm install -g vibelint

# Scan
vibelint scan ./src

# Output
vibelint v0.1.0 — AI Code Pattern Scanner

Files scanned: 47
AI-pattern issues: 12

CRITICAL (3)
  src/api/auth.ts:42
  AI-SEC-001: Hardcoded secret disguised as placeholder
  "sk-placeholder-key-xxx" → move to environment variable
  AI generators produce this 1.88x more often than humans

  src/utils/fetch.ts:18
  AI-LOGIC-001: Async function in .map()
  Returns Promise[], not resolved values
  Fix: Use Promise.all() or for...of

  src/pages/dashboard.tsx:91
  AI-SEC-002: Unsanitized user HTML (dangerouslySetInnerHTML)
  AI code is 2.74x more likely to introduce XSS

WARNING (5) ...
INFO (4) ...

# CI/CD
vibelint scan ./src --format sarif --fail-on critical
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Core engine | Python (can scan any language via AST/regex) |
| JS/TS parsing | Tree-sitter or custom regex patterns |
| Python parsing | AST module + regex patterns |
| CLI | Python (Click/Typer) |
| Config | YAML (Pydantic) |
| Output | Terminal, JSON, SARIF |
| Distribution | PyPI + npm (thin wrapper) |
| CI/CD | GitHub Action (vibelint/action) |

---

## Growth Path

| Phase | What | Timeline |
|---|---|---|
| v0.1 | 15 rules, JS/TS + Python, CLI | Weeks 1-3 |
| v0.2 | 30+ rules, Go + Rust, GitHub Action | Month 2 |
| v0.3 | Community rule contributions, rule marketplace | Month 3 |
| v0.4 | IDE extensions (VS Code, JetBrains) | Month 4 |
| v1.0 | Team dashboard, historical trends, AI debt tracking | Month 6 |

---

## Relationship to Canary

VibeLint and Canary are **independent products** built in parallel.

- VibeLint runs on Canary's codebase during development (dogfooding)
- VibeLint could optionally serve as a quality evaluator inside Canary (for agents that generate code)
- They share no code dependencies — separate repos, separate communities
- Both are OSS, both target developers, both can stand alone

---

## Key References

- [CodeRabbit: AI vs Human Code Report](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)
- [CMU Benchmark: 10.5% pass security](https://dev.to/solobillions/i-tested-every-vibe-coding-security-scanner-2026-heres-what-actually-works-p9k)
- [Survey of Bugs in AI-Generated Code](https://arxiv.org/html/2512.05239v1)
- [AI Tech Debt: 110K+ issues](https://arxiv.org/html/2603.28592)
- [Stack Overflow: 66% fix AI code](https://stackoverflow.blog/2025/12/29/developers-remain-willing-but-reluctant-to-use-ai-the-2025-developer-survey-results-are-here/)
- [eslint-plugin-llm-core](https://dev.to/pertrai1/i-analyzed-500-ai-coding-mistakes-and-built-an-eslint-plugin-to-catch-them-jme)
- [Lint Against the Machine](https://medium.com/@montes.makes/lint-against-the-machine-a-field-guide-to-catching-ai-coding-agent-anti-patterns-3c4ef7baeb9e)
- [SonarQube Agentic Analysis](https://securityboulevard.com/2026/03/sonarqube-agentic-analysis-verify-ai-code-as-it-is-generated/)
- [Semgrep Multimodal](https://www.helpnetsecurity.com/2026/03/20/semgrep-multimodal-code-security/)
