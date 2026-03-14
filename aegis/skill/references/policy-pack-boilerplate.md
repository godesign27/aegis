# Policy Pack: Boilerplate

Version: 1.0.0
Description: General-purpose policy pack for Tailwind CSS + React projects.
Covers common token patterns, standard accessibility requirements, and
typical component structure conventions. Suitable for projects without a
custom design system.

---

## Token Rules

### color.no-hardcoded-values
Severity: HIGH
Description: All color values must use CSS custom properties or Tailwind
config-defined classes. Arbitrary hex, rgb, hsl, and named CSS colors are forbidden.

Forbidden patterns:
- Any hex color: `#[0-9a-fA-F]{3,8}`
- Any rgb/rgba/hsl/hsla function call
- CSS named colors (red, blue, green, etc.) in style props
- Tailwind arbitrary color classes: `text-[#...]`, `bg-[#...]`, `border-[#...]`

Allowed exceptions:
- `transparent`
- `currentColor`
- `inherit`
- `white` and `black` ONLY when used as Tailwind's `text-white`, `bg-black`, etc.
  (standard Tailwind palette classes are allowed; arbitrary values are not)

### spacing.no-hardcoded-values
Severity: MEDIUM
Description: Spacing values must use Tailwind's spacing scale or CSS custom properties.
Inline px/rem spacing values are forbidden in production components.

Forbidden patterns:
- Inline style spacing: `style={{ margin: '12px' }}`, `style={{ padding: '8px 16px' }}`
- Tailwind arbitrary spacing: `p-[13px]`, `mt-[22px]`, `gap-[11px]`

Allowed exceptions:
- `0`, `100%`, `auto`, `min-content`, `max-content`
- Tailwind standard spacing scale: `p-4`, `mt-2`, `gap-6` (numeric scale only)

### typography.no-hardcoded-values
Severity: HIGH
Description: Font sizes, weights, and families must use Tailwind typography classes
or CSS custom properties.

Forbidden patterns:
- Inline font-size: `style={{ fontSize: '14px' }}`
- Inline font-weight: `style={{ fontWeight: 600 }}`
- Inline font-family: `style={{ fontFamily: 'Inter' }}`
- Tailwind arbitrary type: `text-[14px]`, `font-[550]`

Allowed exceptions:
- Standard Tailwind text classes: `text-sm`, `text-base`, `text-lg`, `text-xl`, etc.
- Standard Tailwind font-weight: `font-normal`, `font-medium`, `font-semibold`, `font-bold`

---

## Component Rules

### components.approved-packages
Severity: CRITICAL
Description: Components must be imported from approved packages only. Importing UI
components from unapproved third-party libraries is forbidden.

Default approved packages for boilerplate:
- `react` and `react-dom`
- `react-router-dom` or `@tanstack/router`
- `@radix-ui/*` (headless primitives — acceptable base)
- `lucide-react` (icons)
- `clsx` or `classnames` (utility)
- `tailwind-merge`

Packages that require policy review before use:
- `@mui/material` — only if explicitly added to project policy
- `antd` — only if explicitly added
- `chakra-ui` — only if explicitly added
- Any UI kit not listed above

### components.no-duplicate-primitives
Severity: HIGH
Description: AI must not implement custom versions of components that already exist
in the codebase or approved packages. Check for custom button, input, modal,
card, and badge components when standard versions are available.

### components.no-deprecated
Severity: MEDIUM
Description: AI must not use deprecated component APIs. Check the source repo's
CHANGELOG or deprecation notices.

---

## Accessibility Rules

### a11y.interactive-semantics
Severity: CRITICAL
Description: Interactive elements must use semantic HTML. Non-semantic elements
with click handlers must also have keyboard handlers and appropriate ARIA roles.

Required:
- `<button>` for all click actions (not `<div onClick>` or `<span onClick>`)
- `<a href>` for navigation (not `<div onClick>` for links)
- `role="button"` + `tabIndex={0}` + `onKeyDown` if a non-button is used (flagged MEDIUM)

### a11y.images-require-alt
Severity: HIGH
Description: All `<img>` elements must have an `alt` attribute. Decorative images
must use `alt=""`. Informational images must have a descriptive alt.

### a11y.form-labels
Severity: HIGH
Description: All form inputs must have associated labels via `<label htmlFor>`,
`aria-label`, or `aria-labelledby`.

### a11y.heading-hierarchy
Severity: MEDIUM
Description: Heading levels must not skip. A page must have exactly one `<h1>`.
Levels must increment by one (h1 → h2 → h3).

### a11y.focus-management
Severity: MEDIUM
Description: Custom interactive components must have visible focus styles.
`outline: none` without a `focus-visible` replacement is forbidden.

### a11y.aria-validity
Severity: HIGH
Description: All ARIA attributes must be valid for their element's role.
`aria-hidden="true"` must not be applied to focusable elements.

---

## Pattern Rules

### patterns.no-inline-styles-for-layout
Severity: LOW
Description: Layout properties (display, flexbox, grid, position) should use
Tailwind classes, not inline styles. Exceptions allowed for truly dynamic values
that cannot be expressed as Tailwind classes.

### patterns.consistent-event-handlers
Severity: LOW
Description: Event handler naming must be consistent. Use `handle` prefix for
handlers defined in the component (`handleClick`, `handleSubmit`). Use `on` prefix
for prop names passed to children (`onClick`, `onSubmit`).

---

## Hallucination Watchlist

Known-bad patterns to always flag:

### Common hallucinated packages
- Any `@company/*` package that doesn't exist in the source repo's package.json
- `react-query` imported as `@tanstack/react-query` v3 syntax (API changed in v4/v5)
- `next/router` in a non-Next.js project
- `gatsby` imports in a non-Gatsby project

### Common hallucinated component patterns
- `<Icon name="..." />` — check that an Icon component with this API actually exists
- `<Typography variant="..." />` — check that Typography from this source has variant prop
- `<Grid container spacing={...} />` — MUI-specific API; flag if MUI not in package.json
- `useTheme()` hook — verify the theme provider is actually present in the source repo

### Common hallucinated token patterns
- `var(--color-brand-*)` — verify these exist in the source's CSS custom properties
- `var(--spacing-*)` — verify spacing tokens are actually defined
- Any Tailwind class using keys not in tailwind.config.js (e.g. `text-brand-primary`
  when the config doesn't extend with brand colors)
