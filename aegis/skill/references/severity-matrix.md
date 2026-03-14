# Severity Matrix

Use this matrix to assign severity to findings. When multiple rules apply to
a single finding, assign the highest applicable severity.

---

## Severity Levels

### CRITICAL
**API behavior**: `status: blocked`
**Definition**: The violation will break the build, cause a runtime crash, create
a security exposure, or make the UI completely unusable for assistive technology users.

Assign CRITICAL when:
- Import from a non-existent package (build-breaking)
- Reference to a non-existent component export (build-breaking)
- Interactive element with no keyboard handling AND no semantic role (completely
  inaccessible to keyboard users)
- Import from wrong design system package entirely (e.g. MUI when project uses
  Radix — architectural violation)
- Hardcoded secret or environment variable exposed in UI code

### HIGH
**API behavior**: `status: blocked`
**Definition**: The violation is a clear design system breach that should not reach
production without deliberate review. Will cause visible inconsistency or significant
accessibility failure.

Assign HIGH when:
- Hardcoded production-visible color values (users will see non-token colors)
- Missing aria-label on icon-only buttons or interactive elements
- Missing alt attribute on informational images
- Form input without any label association
- Non-existent CSS custom property reference (silent runtime failure)
- Unapproved UI library import when an approved alternative exists
- shadcn/ui import without shadcn being set up in the project
- Lovable's systemic arbitrary color pattern (counts as HIGH not MEDIUM because
  it's pervasive)
- Any hallucinated component that will fail silently at runtime

### MEDIUM
**API behavior**: `status: warned`
**Definition**: A real policy violation that should be fixed but doesn't block
deployment on its own. Accumulation of MEDIUM issues indicates systemic drift.

Assign MEDIUM when:
- Hardcoded spacing values in layout-critical components
- Deprecated component with available replacement
- Heading hierarchy violation
- tabIndex > 0 (breaks natural tab order)
- File placed in wrong directory relative to repo conventions
- CSS architecture mismatch (mixing Tailwind with inline styles against convention)
- State management pattern inconsistent with repo conventions
- `aria-expanded`/`aria-controls` missing on disclosure widgets
- Custom component duplicating an existing approved component

### LOW
**API behavior**: `status: passed` (but findings still reported)
**Definition**: A suggestion-level issue. The code works and is accessible but
deviates from preferred patterns.

Assign LOW when:
- Naming convention inconsistency (prop names, file names)
- Missing optional but beneficial ARIA attributes
- Minor inline style for layout (when overall architecture is correct)
- Pattern that works but is inconsistent with the repo's established conventions
- Documentation or comment style inconsistency

### INFO
**API behavior**: `status: passed`
**Definition**: An observation with no compliance impact. Contextual information
that may be useful for the developer or for audit trail purposes.

Assign INFO when:
- Files added by the AI that are structurally sound but weren't in the source repo
  (informing the developer of additions, not violations)
- Package.json additions that appear intentional and safe
- Structural observations about how the AI interpreted the design
- Statistics about the scope of changes (N files modified, M components added)

---

## Aggregation Rules

When computing the top-level `status` for an audit:

1. Any CRITICAL finding → `status: blocked`
2. Any HIGH finding (no CRITICAL) → `status: blocked`
3. Only MEDIUM findings (no CRITICAL or HIGH) → `status: warned`
4. Only LOW/INFO findings → `status: passed`

The `status: blocked` result means the API caller (CI/CD pipeline, AI tool) should
prevent the generated code from being merged or deployed without human review.

The `status: warned` result means the code can proceed but the developer should
review and address the MEDIUM findings in the next iteration.

The `status: passed` result means the code is compliant with the active policy pack.

---

## Severity Adjustment by Context

**Volume-based escalation**: If more than 8 findings of the same rule are found in
a single audit, escalate the overall severity for that rule by one level. A pattern
of 10+ MEDIUM token violations signals a systemic issue that warrants the same
attention as a HIGH finding.

**Regression vs. new violation**: In comparison mode, a violation introduced by the
AI in previously-clean code should be weighted higher than the same violation found
in code the AI didn't touch. The diff boundary matters.

**Blocked but fixable**: When assigning CRITICAL or HIGH, always note whether the
fix is deterministic (same value can always be substituted) or requires human judgment
(ambiguous design intent). This helps the developer triage quickly.
