# Tool Profiles

Known behavioral patterns for each AI coding tool. Load this file when the
`tool_type` field is known. Use these profiles to improve detection accuracy
and tune severity assignments.

---

## Bolt.new

### Behavioral signature
Bolt generates full-stack React applications from prompts. It tends to produce
complete, deployable codebases rapidly but with predictable governance weaknesses.

### Known patterns

**Token violations (HIGH frequency)**
- Bolt frequently hardcodes hex colors in Tailwind `className` arbitrary values:
  `className="text-[#6366f1] bg-[#f8fafc]"`
- Bolt uses inline `style={{}}` objects for one-off spacing adjustments rather
  than extending the Tailwind config
- Font families are often hardcoded in `tailwind.config.js` as literal strings
  rather than using CSS custom properties

**Component patterns**
- Bolt tends to scaffold `lucide-react` icons correctly but sometimes invents
  icon names that don't exist in the installed version. Always verify icon names
  against the lucide-react export list.
- Bolt may duplicate a Button or Card component inline in a page file even when
  a shared version already exists
- Bolt sometimes generates components that import from each other circularly —
  flag any circular dependency patterns

**Accessibility patterns**
- Bolt generally produces semantic HTML for simple layouts but regresses on
  complex interactive patterns: custom dropdowns, modals, and tooltips often
  lack keyboard handling and ARIA
- Icon-only buttons frequently missing `aria-label`
- Bolt often omits `<label>` elements on form inputs, using `placeholder` as the
  only text identifier

**Scope patterns**
- Bolt sometimes restructures the entire App.tsx or routing layer when the prompt
  only requested a single component. Flag any routing changes as design system drift
  unless routing was explicitly in scope.
- Bolt tends to add dependencies to package.json without the developer requesting
  them. Always diff package.json and flag new additions for review.

### Recommended severity adjustments
- Bolt icon name hallucinations: always CRITICAL (build-breaking)
- Bolt package.json additions: flag as HIGH for human review
- Bolt routing restructures: flag as HIGH design system drift

---

## Lovable.dev

### Behavioral signature
Lovable generates React + Tailwind applications with a focus on visual quality.
It produces polished UIs but has distinct governance weaknesses around token usage
and component sourcing.

### Known patterns

**Token violations (VERY HIGH frequency)**
- Lovable's primary weakness: it generates beautiful UIs using hardcoded values
  extensively. Expect a high volume of token violations in every Lovable audit.
- Lovable uses Tailwind arbitrary values prolifically: `bg-[#F5F5F5]`, `text-[14px]`,
  `h-[calc(100vh-64px)]`
- Lovable often generates a custom color palette directly in component classNames
  rather than extending tailwind.config.js — this is a systemic pattern violation

**Component patterns**
- Lovable frequently introduces shadcn/ui components without checking whether
  they're installed in the project. Always check the source repo for shadcn/ui setup
  before accepting shadcn imports.
- Lovable imports from `@/components/ui/*` — this is the shadcn path convention.
  Flag if these components don't exist in the source repo.
- Lovable may generate a full component library in `components/ui/` even when one
  already exists — check for duplication

**Accessibility patterns**
- Lovable produces better semantic HTML than Bolt on average, but still regresses
  on ARIA for complex components
- Custom animated components (drawers, accordions) from Lovable often lack proper
  ARIA state attributes (`aria-expanded`, `aria-controls`)

**Scope patterns**
- Lovable tends to stay closer to the requested scope than Bolt — routing changes
  are less common
- However, Lovable may introduce Tailwind config modifications as a side effect of
  generating custom color schemes. Flag any tailwind.config.js changes.

### Recommended severity adjustments
- Tailwind arbitrary color values in Lovable output: HIGH (systemic pattern, not one-off)
- shadcn/ui imports without setup: CRITICAL
- Tailwind config modifications: HIGH (requires design system review)

---

## Figma Make

### Behavioral signature
Figma Make generates UI code directly from Figma designs. Its output is
design-accurate but has unique governance challenges because it operates from
visual specs rather than code intent.

### Known patterns

**Token violations (HIGH frequency, different character)**
- Figma Make extracts exact values from the Figma file — these are often correct
  design values but expressed as hardcoded literals rather than tokens
- Common pattern: `color: '#1A1A2E'` where the Figma file has a named color style
  "Brand/Primary Dark" — the value is correct but the token reference is missing
- Spacing values extracted from Figma auto-layout are almost always hardcoded px values

**Component patterns**
- Figma Make generates component structures that mirror the Figma component tree,
  which may not match the codebase's component architecture
- Frame-to-div mapping: Figma frames become `<div>` elements — flag cases where
  a semantic element (`<section>`, `<article>`, `<nav>`) would be more appropriate
- Figma Make sometimes generates deeply nested div structures (div soup) that
  match the Figma layer hierarchy but violate HTML best practices

**Accessibility patterns**
- Figma Make is the weakest of the three tools on accessibility — Figma designs
  rarely carry ARIA metadata, so the generated code inherits nothing
- Expect missing alt attributes on all images (Figma image layers have no alt context)
- All interactive elements from Figma Make should be audited for keyboard handling
- Text that looks like a heading in Figma is often a styled `<p>` or `<div>`, not
  an `<h1>`-`<h6>` — heading hierarchy violations are very common

**Scope patterns**
- Figma Make is the most faithful to scope — it generates what's in the Figma frame
  and typically doesn't restructure the rest of the codebase
- However, it may generate standalone CSS files or inject global styles that conflict
  with the existing CSS architecture

### Recommended severity adjustments
- Figma-extracted hardcoded color values: HIGH (systemic — every value will be hardcoded)
- Missing alt attributes from Figma image layers: HIGH (expected pattern, still a violation)
- Div soup / missing semantic elements: MEDIUM
- Global style injection: HIGH (CSS architecture conflict)

---

## Unknown / Generic AI Tool

When tool_type is unknown, apply standard boilerplate analysis without
tool-specific heuristic adjustments. Look for patterns from all three profiles
and note in findings if a pattern is recognizable as tool-specific.
