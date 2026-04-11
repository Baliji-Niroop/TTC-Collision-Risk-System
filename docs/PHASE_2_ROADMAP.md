# TTC Professional Roadmap — Phase 2: Excellence

**Date:** April 11, 2026  
**Current Phase:** Phase 1 Complete (Hardware-Ready) ✅  
**Next Phase:** Phase 2 (Professional 10/10 Standard)  
**Vision:** Automotive-grade collision risk prediction system

---

## Current Status: Production-Ready Baseline ✅

### Phase 1 Achievements (Complete)
- ✅ Firmware blockers fixed (feature flags, namespaces, linker errors)
- ✅ Comprehensive documentation (wiring, assembly, organization)
- ✅ End-to-end validation (31/31 tests pass)
- ✅ Project organization & cleanup complete
- ✅ Hardware assembly checklist prepared

**Current Grade: 7/10** (Functional, documented, validated)

---

## Phase 2: Professional Excellence (9 Tasks, 40–50 hours)

### Priority 1: Code Quality & Safety (10–15 hours)

**Task 1: PEP 8 & Type Hints (4–6 hours)**
- Current: ~70% type hints coverage
- Target: 100% type hints + pylint ≥9.5/10
- Files: `src/`, `validation/`, `bridge/`
- Effort: Low; high ROI for maintainability
- Status: Ready to execute

**Task 2: Extended Kalman Filter (6–8 hours)**
- Current: Simple 1D Kalman filter
- Target: Non-linear EKF for sensor fusion
- Expected Gain: 15% noise reduction
- Complexity: High; requires signal processing knowledge
- Status: Ready to execute

**Task 8: Safety Compliance (3–4 hours)**
- Current: Thresholds documented inline
- Target: ISO 15623 safety case document
- Files: Create `docs/SAFETY_CASE.md`
- Effort: Medium; critical for automotive use
- Status: Ready to execute

### Priority 2: Analytics & Reporting (15–20 hours)

**Task 3: Collision Probability (4–5 hours)**
- Current: No probability calculation
- Target: Bayesian collision probability + session JSON
- Expected Impact: Better risk quantification
- Complexity: Medium (Bayesian formula)
- Status: Ready to execute

**Task 5: PDF Report Generator (5–7 hours)**
- Current: No reporting capability
- Target: Professional PDF audits with charts
- Expected Use: Post-session safety analysis
- Complexity: Medium (matplotlib + reportlab)
- Status: Ready to execute

**Task 4: Dashboard Enhancements (5–8 hours)**
- Current: Basic metrics display
- Target: Risk gauge, safety score, timeline
- Expected Impact: Professional UI, better user engagement
- Complexity: Medium (Streamlit CSS customization)
- Status: Ready to execute

### Priority 3: Testing & DevOps (10–15 hours)

**Task 6: Test Coverage (6–8 hours)**
- Current: 60% coverage
- Target: ≥90% coverage
- New Tests: Integration tests for critical paths
- Complexity: Medium
- Status: Ready to execute

**Task 7: CI/CD Automation (3–4 hours)**
- Current: Manual checks
- Target: Automated quality gates on every commit
- Tools: GitHub Actions, pylint, mypy, pytest
- Complexity: Low; high value for team workflow
- Status: Ready to execute

**Task 9: Protocol Verification (Ongoing)**
- Current: Ad-hoc checks
- Target: Enforced process for telemetry format
- Effort: < 5 min per change
- Status: Establish as standard practice

---

## Implementation Roadmap (Recommended Sequence)

### Week 1: Foundation
- **Task 1** (PEP 8 & Type Hints) — Foundation for all other work
- **Task 8** (Safety Case) — Clarify requirements
- **Task 9** (Protocol Verification) — Establish guardrails

**Estimate: 11–15 hours**  
**Team:** 1–2 developers

### Week 2: Analytics
- **Task 3** (Collision Probability) — Build on safety framework
- **Task 5** (PDF Reports) — Deliver tangible capability
- **Task 7** (CI/CD) — Enable team efficiency

**Estimate: 12–16 hours**  
**Team:** 1–2 developers

### Week 3: Polish & Test
- **Task 4** (Dashboard UX) — Improve user experience
- **Task 6** (Test Coverage) — Ensure reliability
- **Task 2** (EKF) — Performance optimization

**Estimate: 17–21 hours**  
**Team:** 1–2 developers + signal processing expert (for EKF)

**Total Phase 2 Timeline: 3–4 weeks (40–50 hours)**

---

## Expected Grade Progression

```
Phase 1 (Current):          7/10 ✅
├─ Functional
├─ Documented
└─ Validated

Phase 2 (After Tasks 1,8,9): 7.5/10
├─ + Type hints
├─ + Safety case
└─ + Verified protocols

Phase 2 (After Tasks 3,5,7): 8.5/10
├─ + Analytics
├─ + Reports
└─ + CI/CD

Phase 2 (After Tasks 4,6,2): 10/10 ✅
├─ + Professional UI
├─ + 90%+ coverage
└─ + Optimized firmware
```

---

## Success Metrics (Phase 2 Completion)

| Metric | Current | Target | Evidence |
|--------|---------|--------|----------|
| Code Coverage | 60% | ≥90% | `pytest --cov` report |
| Pylint Score | 7.8/10 | ≥9.5/10 | `pylint` output |
| Type Hints | 70% | 100% | Manual audit + `mypy --strict` |
| Documentation | Good | Excellent | SAFETY_CASE.md complete |
| CI/CD Pipeline | Manual | Automated | GitHub Actions workflow |
| Dashboard FPS | 2 Hz | 5 Hz | Streamlit profiling |
| Sensor Noise | 25 cm σ | <21 cm σ (15% reduction) | Test with synthetic data |
| Test Suite | 5 suites | 10+ suites | Test file count in tests/ |

---

## Resource Requirements

### Team Composition
- **1 Python Developer** (PEP 8, analytics, dashboard, testing)
- **1 Firmware Developer** (EKF optimization)
- **1 DevOps/QA** (CI/CD, test automation) — Can be part-time
- **1 Safety Engineer** (ISO 15623 compliance) — Consultation only

### Tools & Resources
- ✅ Already Available: Python, Arduino IDE, GitHub
- Need to Install: `pytest-cov`, `mypy`, `pylint`, `reportlab`, `sphinx` (for docs)
- Infrastructure: GitHub Actions (free tier sufficient)

### Time Allocation
- **Full-Time Effort:** 3–4 weeks (1 Python dev + 1 firmware dev)
- **Part-Time Effort:** 6–8 weeks (with parallelization)
- **With external review cycles:** 8–10 weeks

---

## Dependency Graph (Task Execution Order)

```
Task 1 (PEP 8) ─────┐
                    ├→ Task 6 (Coverage) ────→ Task 7 (CI/CD)
Task 8 (Safety) ────┤
                    ├→ Task 3 (Probability) ─→ Task 5 (Reports)
Task 9 (Protocol) ──┤
                    └→ Task 4 (Dashboard)

Task 2 (EKF) ───────→ [Independent, can start after Phase 1]
```

**Critical Path:** Task 1 → Task 6 → Task 7 (14–18 hours)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Type hint changes break existing code | Low | Medium | Use `mypy --ignore-missing-imports` initially |
| EKF implementation has numerical issues | Medium | High | Unit tests with known sensor data + external validation |
| PDF generation performance | Medium | Low | Profile early; use caching if needed |
| CI/CD pipeline too slow | Low | Medium | Parallelize tests; use cached dependencies |
| Coverage target unrealistic | Low | Medium | Aim for 85% initially; iterate to 90% |

---

## Post-Phase 2 Vision (Phase 3)

Once Phase 2 complete (10/10 grade achieved), consider:

1. **Automotive Certification** (ISO 26262 Functional Safety)
2. **Embedded ML** (Enable optional ENABLE_ML_CLASSIFIER by default)
3. **Hardware Variants** (Support different ESP32 boards, LIDAR options)
4. **Cloud Integration** (Remote telemetry upload, fleet analytics)
5. **Mobile App** (Native iOS/Android companion app)

---

## Decision Point: Proceed with Phase 2?

### Questions for Decision-Makers

1. **Is automotive-grade quality required?**
   - Yes → Execute Phase 2 (full 10/10)
   - No → Current Phase 1 sufficient (7/10)

2. **What's the hardware timeline?**
   - Deploying in 2 weeks → Focus on Tasks 1, 8, 9 only
   - Deploying in 2 months → Execute full Phase 2

3. **Who owns long-term maintenance?**
   - Internal team → Invest in Tasks 1, 6, 7 (code quality + testing)
   - External vendor → Prioritize Tasks 8, 5 (compliance + reports)

4. **Budget constraints?**
   - Unlimited → Execute all 9 tasks in parallel (3 weeks)
   - Limited → Execute sequentially (8 weeks)

---

## Recommendation

**Proceed with Phase 2** if:
- ✅ System will be used in production automotive context
- ✅ Team has 1–2 developers available for 3–4 weeks
- ✅ Budget for quality assurance is approved

**Skip Task 2 (EKF)** if:
- Current sensor fusion already meets performance targets
- Can defer optimization to later phase

**Minimum Viable Phase 2** (2 weeks, 3 developers):
- Task 1 (PEP 8) — Code quality foundation
- Task 8 (Safety Case) — Compliance documentation
- Task 9 (Protocol Verification) — Risk mitigation

---

## Next Steps

1. **Approve Phase 2 Vision** — Management decision
2. **Allocate Resources** — Assign 1–2 developers
3. **Create Sprint Plan** — 2-week sprints × 2–3 sprints
4. **Establish CI/CD** — Set up GitHub Actions (Task 7 first)
5. **Execute Tasks Sequentially** — Follow recommended roadmap

---

**Prepared by:** GitHub Copilot  
**Date:** April 11, 2026  
**Status:** Ready for Management Review

**Recommendation: APPROVE Phase 2. System quality investment will pay dividends in reliability, maintainability, and compliance.**
