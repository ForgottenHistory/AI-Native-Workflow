# CONSTRAINTS

**Version:** 1.0
**Date:** YYYY-MM-DD
**Project:** [Name]

---

## Global Rules

### NEVER
- ❌ [Forbidden practice 1] - **Why:** [Rationale]
- ❌ [Forbidden practice 2] - **Why:** [Rationale]

### ALWAYS
- ✅ [Required practice 1] - **Why:** [Rationale]
- ✅ [Required practice 2] - **Why:** [Rationale]

### SHOULD (Guidelines)
- 💡 [Guideline 1]
- 💡 [Guideline 2]

---

## Performance Budgets

### Load Time
- **Maximum:** [X seconds] on 3G
- **Target:** [Y seconds] on broadband
- **Check:** Run Lighthouse performance audit

### Bundle Size
- **Maximum:** [X KB] total (gzipped)
- **Breakdown:**
  - HTML: [A KB]
  - CSS: [B KB]
  - JS: [C KB]
- **Check:** `npm run build && du -sh dist/`

---

## Accessibility

- **Standard:** WCAG 2.1 Level AA compliance
- **Lighthouse Score:** Minimum 95
- **Required:**
  - Semantic HTML throughout
  - Keyboard navigable
  - ARIA labels on interactive elements
  - Color contrast ≥ 4.5:1
- **Check:** Lighthouse accessibility audit + manual keyboard testing

---

## Testing Requirements

### Required Tests
- ✅ [Test type 1]: [What must be validated]
- ✅ [Test type 2]: [What must be validated]

### Coverage Target
- **Minimum:** [X%] code coverage
- **Check:** `npm test -- --coverage`

---

## Security

- [Security constraint 1]
- [Security constraint 2]

---

## Technology Constraints

### Allowed
- ✅ [Technology/pattern 1]
- ✅ [Technology/pattern 2]

### Forbidden
- ❌ [Technology/pattern 1] - **Why:** [Rationale]
- ❌ [Technology/pattern 2] - **Why:** [Rationale]

---

## Documentation Requirements

- README.md with setup instructions
- Inline comments for complex logic
- Architecture decisions documented

---

## Constraint Validation

| Constraint | How to Check | Automated? |
|-----------|--------------|------------|
| [Constraint 1] | [Command/process] | Yes/No |
| [Constraint 2] | [Command/process] | Yes/No |

---

## Notes

[Additional context about constraints]
