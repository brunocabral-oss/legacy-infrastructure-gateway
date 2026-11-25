## Description
Provide a brief summary of the changes introduced in this pull request.

## Related Issue
Fixes #[Issue Number] / Related to #[Issue Number]

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New vendor driver / feature (non-breaking change which adds functionality)
- [ ] Semantic normalization update
- [ ] Breaking change (fix or feature that would cause existing vendor integration tests to fail)
- [ ] Documentation update

## Engineering & Safety Checklist
- [ ] **Read-Only Compliance:** Confirmed that all integration queries and operations respect the read-only safety policy unless explicitly authorized.
- [ ] **Vendor Driver Isolation:** Changes to vendor drivers are modular, cleanly encapsulated, and do not leak vendor-specific anomalies into core LIG domain logic.
- [ ] **Semantic Normalization:** Verified that normalized output schemas match expected standard domain models.
- [ ] **Contract Tests:** Added or updated contract tests (`pytest`) covering the new behavior or bug fix.
- [ ] **Zero-Exposure Policy:** Ensured no sensitive data, internal IP schemas, or credentials are hardcoded or exposed in logs/tests.

## Testing & Verification
Describe the tests performed to verify your changes:
- [ ] Unit / Contract Tests passed locally (`pytest`)
- [ ] Sandbox / Integration smoke tests verified
