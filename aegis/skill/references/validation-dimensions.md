# Validation Dimensions

Detection logic for each of the five audit dimensions.

---

## 1. Token Violations

Design tokens are named references to design decisions (colors, spacing, typography).
A token violation occurs when AI-generated code uses a raw value instead of the token.

### What to detect

**Color violations**
- Hardcoded hex values: `#3B82F6`, `#ffffff`, `#1f2937`
- Hardcoded rgb/hsl: `rgb(59, 130, 246)`, `hsl(217, 91%, 60%)`
- Tailwind arbitrary color values: `text-[#3B82F6]`, `bg-[#1f2937]`
- Named CSS colors: `color: blue`, `background: red`
- Exception: `transparent`, `inherit`, `currentColor` are always allowed

**Spacing violations**
- Hardcoded px margins/padding: `margin: 12px`, `padding: 8px 16px`
- Hardcoded rem values not mapped to a token: `gap: 0.75rem` (if 0.75rem is not a
  token value in the active policy pack)
- Tailwind arbitrary spacing: `p-[13px]`, `mt-[22px]`
- Exception: `0`, `100%`, `auto`, `min-content`, `max-content` are always allowed

**Typography violations**
- Hardcoded font-size: `font-size: 14px`, `font-size: 0.875rem`
- Hardcoded font-weight: `font-weight: 600` (if 600 is not a token)
- Hardcoded font-family: `font-family: 'Inter', sans-serif` (should use token)
- Tailwind arbitrary typography: `text-[14px]`, `font-[550]`

### Severity guidance
- Production-visible color hardcode → HIGH
- Spacing hardcode in a core layout component → MEDIUM
- Typography hardcode on a heading element → HIGH
- Minor spacing on a non-critical element → LOW

---

## 2. Component Violations

Component violations occur when the AI uses the wrong component, wrong import path,
wrong composition, or wrong prop usage relative to the design system.

### What to detect

**Unapproved component usage**
- Component names not in the policy pack's approved component list
- Importing components from wrong packages (e.g. `import Button from '@mui/material'`
  when the policy pack specifies `@company/design-system`)
- Custom inline components that duplicate approved ones (e.g. defining a local
  `<MyButton>` when `<Button>` from the design system should be used)

**Wrong composition**
- Missing required wrapper components (e.g. `<Card>` content without `<CardBody>`)
- Forbidden nesting (e.g. block-level elements inside inline elements)
- Required prop omission (e.g. `<Button>` without `variant` prop when policy
  requires it)
- Deprecated component usage (components in the policy pack's deprecated list)

**Import path violations**
- Importing from a barrel that doesn't exist in the source repo
- Version-pinned imports that conflict with the repo's installed version
- Side-effect-only imports that the policy pack forbids

### Severity guidance
- Wrong design system package altogether → CRITICAL
- Unapproved component when an approved alternative exists → HIGH
- Deprecated component with an available replacement → MEDIUM
- Missing optional prop that improves quality → LOW

---

## 3. Accessibility Regressions

Accessibility regressions occur when AI-generated code degrades the accessibility
of the UI compared to either the source baseline or the policy pack requirements.

### What to detect

**Semantic HTML violations**
- Interactive elements implemented as non-semantic divs/spans:
  `<div onClick={...}>` instead of `<button>`
  `<span onClick={...}>` instead of `<a href>`
- Heading hierarchy violations: skipped levels (h1 → h3), multiple h1s
- Missing landmark elements: no `<main>`, no `<nav>` on navigation components
- Form inputs without associated `<label>` elements

**ARIA violations**
- Missing `aria-label` on icon-only buttons or links
- `aria-hidden="true"` on focusable elements
- Invalid ARIA role usage (role="button" on non-interactive elements without
  keyboard handlers)
- Missing `aria-expanded`, `aria-controls` on disclosure widgets
- `aria-labelledby` pointing to a non-existent element ID

**Keyboard navigation**
- `tabIndex` values greater than 0 (breaks natural tab order)
- `onKeyDown`/`onKeyPress` missing where `onClick` is present on non-native elements
- Focus trap not implemented on modal/dialog components
- Missing `focus-visible` styles (outline: none without a focus-visible replacement)

**Images and media**
- `<img>` without `alt` attribute
- `<img alt="">` on images that appear informational (decorative `alt=""` is valid
  only for purely decorative images)
- `<video>` without captions track

### Severity guidance
- Interactive div without keyboard handler → CRITICAL
- Missing aria-label on icon-only interactive element → HIGH
- Skipped heading level → MEDIUM
- tabIndex > 0 → MEDIUM
- Missing alt on a clearly decorative image → LOW

---

## 4. Design System Drift

Design system drift is systemic divergence from the patterns established in the
source repo. Unlike token or component violations (which are rule-based), drift is
pattern-based — it's about whether the AI's output is consistent with how the
codebase was built.

This dimension only applies in **comparison mode** (when a GitHub baseline is provided).

### What to detect

**File structure drift**
- New files placed in wrong directories (e.g. new component in `src/pages/` when
  all components live in `src/components/`)
- New utility functions placed inline in components instead of `src/utils/`
- Test files missing where the baseline has test coverage for similar components

**Naming convention drift**
- Component files named incorrectly (e.g. `heroSection.tsx` vs the repo's
  `HeroSection.tsx` convention)
- CSS class naming inconsistent with existing patterns
- Prop naming inconsistent with existing component APIs (e.g. `isDisabled` vs
  repo convention `disabled`)

**State management drift**
- AI introduces local `useState` where the repo uses a global store
- AI introduces a new context when an existing context would serve the purpose
- AI uses a different data-fetching pattern than established in the repo

**CSS architecture drift**
- Mixing Tailwind with inline styles when the repo uses Tailwind-only
- Introducing CSS modules when the repo uses styled-components (or vice versa)
- Adding global CSS rules when the repo uses component-scoped styles

### Severity guidance
- CSS architecture mismatch affecting multiple files → HIGH
- File in wrong directory → MEDIUM
- Naming convention violation → LOW
- Structural pattern inconsistency → MEDIUM

---

## 5. Hallucinated Components

Hallucinated components are references to things that don't exist: non-existent
packages, made-up component names, invented token names, or fabricated API methods.
These typically compile (or fail silently at runtime) and are the hardest class of
violation to catch with static analysis.

### What to detect

**Non-existent package imports**
- `import X from 'package-that-doesnt-exist'`
- Verify against: the repo's package.json, the policy pack's approved packages list
- Common hallucinated packages: `@company/icons`, `@company/hooks`, version numbers
  that don't exist (e.g. `react@19.5.0` when latest is lower)

**Non-existent component references**
- `<DesignSystem.TokenPicker>` — component not in any approved package
- `<Grid.AutoFit>` — sub-component that doesn't exist in the installed version
- Components imported from a valid package but that version doesn't export them

**Invented token references**
- CSS custom properties that don't exist: `var(--color-brand-ultralight)`
- Tailwind config keys that aren't in the repo's tailwind config
- Design token names not in the policy pack's token registry

**Made-up API calls / prop patterns**
- Calling methods that don't exist on a library's public API
- Prop names that the component doesn't accept (especially harmful on strict
  TypeScript codebases — but may silently fail in JS)
- Hook signatures that don't match the installed version

### Severity guidance
- Import from a non-existent package → CRITICAL (will break the build)
- Reference to non-existent component export → CRITICAL
- Non-existent CSS custom property → HIGH (silent failure at runtime)
- Invented token name in Tailwind arbitrary value → MEDIUM
- Prop that doesn't exist on a typed component → HIGH
