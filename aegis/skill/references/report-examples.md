# Report Examples

Concrete examples of complete audit reports for format reference.
Use these as templates when generating the final report in Step 7.

---

## Example 1: Blocked (Bolt.new, token + a11y violations)

```json
{
  "audit_id": "aud_01HV5K2MXQJ8FGDP3NW6YBZRT",
  "status": "blocked",
  "tool_type": "bolt",
  "policy_pack": "boilerplate",
  "created_at": "2026-03-13T14:22:05Z",
  "summary": {
    "status": "blocked",
    "total_findings": 7,
    "by_severity": {
      "critical": 0,
      "high": 3,
      "medium": 2,
      "low": 1,
      "info": 1
    },
    "by_dimension": {
      "token_violation": 3,
      "component_violation": 0,
      "accessibility_regression": 2,
      "design_system_drift": 1,
      "hallucinated_component": 1
    },
    "narrative": "Bolt generated a functional hero section and navigation layout that correctly follows the source repo's component structure and routing conventions. However, it introduced three high-severity token violations using hardcoded hex color values and two accessibility regressions on the mobile menu toggle. The hallucinated icon name 'Menu2' does not exist in the installed version of lucide-react and will cause a build failure. Deployment is blocked pending remediation of the HIGH findings."
  },
  "findings": [
    {
      "id": "finding_001",
      "severity": "CRITICAL",
      "dimension": "hallucinated_component",
      "rule": "hallucination.non-existent-export",
      "file": "src/components/Navbar.tsx",
      "line": 3,
      "code_snippet": "import { Menu2 } from 'lucide-react'",
      "violation": "'Menu2' is not exported by lucide-react. The correct icon name is 'Menu'.",
      "expected": "import { Menu } from 'lucide-react'",
      "fix_suggestion": "Replace 'Menu2' with 'Menu'. Lucide uses no numeric suffixes on standard icons.",
      "tool_pattern": "bolt"
    },
    {
      "id": "finding_002",
      "severity": "HIGH",
      "dimension": "token_violation",
      "rule": "color.no-hardcoded-values",
      "file": "src/components/HeroSection.tsx",
      "line": 12,
      "code_snippet": "className=\"bg-[#6366f1] text-[#ffffff]\"",
      "violation": "Arbitrary hex values in Tailwind className bypass the design token system.",
      "expected": "Use approved token classes such as 'bg-primary text-white' or extend tailwind.config.js with named colors.",
      "fix_suggestion": "Replace 'bg-[#6366f1]' with 'bg-primary' and 'text-[#ffffff]' with 'text-white'. If 'bg-primary' is not defined, add it to the Tailwind config's theme.extend.colors.",
      "tool_pattern": "bolt"
    },
    {
      "id": "finding_003",
      "severity": "HIGH",
      "dimension": "token_violation",
      "rule": "color.no-hardcoded-values",
      "file": "src/components/HeroSection.tsx",
      "line": 28,
      "code_snippet": "style={{ background: '#f8fafc', borderColor: '#e2e8f0' }}",
      "violation": "Hardcoded hex values in inline style object.",
      "expected": "Use CSS custom properties: var(--color-surface) and var(--color-border).",
      "fix_suggestion": "Replace with Tailwind classes 'bg-slate-50 border-slate-200' or define CSS custom properties matching these values.",
      "tool_pattern": "bolt"
    },
    {
      "id": "finding_004",
      "severity": "HIGH",
      "dimension": "accessibility_regression",
      "rule": "a11y.interactive-semantics",
      "file": "src/components/MobileMenu.tsx",
      "line": 8,
      "code_snippet": "<div className=\"cursor-pointer\" onClick={toggleMenu}>",
      "violation": "Clickable div is not keyboard accessible and lacks semantic role.",
      "expected": "Use <button> element for click actions.",
      "fix_suggestion": "Replace '<div onClick={toggleMenu}>' with '<button onClick={toggleMenu} aria-expanded={isOpen} aria-label=\"Toggle navigation menu\">'. This provides keyboard access and screen reader context.",
      "tool_pattern": "bolt"
    },
    {
      "id": "finding_005",
      "severity": "HIGH",
      "dimension": "token_violation",
      "rule": "typography.no-hardcoded-values",
      "file": "src/components/HeroSection.tsx",
      "line": 35,
      "code_snippet": "style={{ fontSize: '56px', fontWeight: 700, letterSpacing: '-0.02em' }}",
      "violation": "Hardcoded typography values in inline style.",
      "expected": "Use Tailwind typography classes for all type settings.",
      "fix_suggestion": "Replace with 'className=\"text-6xl font-bold tracking-tight\"' which maps to equivalent values in Tailwind's default scale.",
      "tool_pattern": "bolt"
    },
    {
      "id": "finding_006",
      "severity": "MEDIUM",
      "dimension": "accessibility_regression",
      "rule": "a11y.aria-validity",
      "file": "src/components/MobileMenu.tsx",
      "line": 22,
      "code_snippet": "<nav aria-label=\"mobile\" className={isOpen ? 'block' : 'hidden'}>",
      "violation": "Navigation is hidden with CSS 'hidden' class but aria-label suggests it should be screen-reader accessible. Hidden elements should use aria-hidden or display:none for consistency.",
      "expected": "Add aria-hidden={!isOpen} to prevent screen readers from reaching hidden navigation.",
      "fix_suggestion": "Add aria-hidden={!isOpen} to the <nav> element, or use a proper disclosure pattern with aria-expanded on the toggle button and conditional rendering.",
      "tool_pattern": "bolt"
    },
    {
      "id": "finding_007",
      "severity": "INFO",
      "dimension": "design_system_drift",
      "rule": "patterns.new-files",
      "file": "src/components/MobileMenu.tsx",
      "line": null,
      "code_snippet": null,
      "violation": "MobileMenu.tsx is a new file added by the AI with no counterpart in the source repo.",
      "expected": "No violation — new files are expected. This is an informational observation.",
      "fix_suggestion": "Review MobileMenu.tsx to confirm it aligns with the project's component conventions. Consider moving mobile menu logic into Navbar.tsx if the component is small.",
      "tool_pattern": "bolt"
    }
  ],
  "diff_summary": {
    "files_added": ["src/components/MobileMenu.tsx", "src/components/HeroSection.tsx"],
    "files_modified": ["src/components/Navbar.tsx", "src/App.tsx"],
    "files_removed": [],
    "files_unchanged": 18,
    "baseline_commit": "a3f8c91d"
  },
  "policy_pack_version": "1.0.0",
  "aegis_version": "1.0.0"
}
```

---

## Example 2: Passed (Figma Make, minor findings only)

```json
{
  "audit_id": "aud_01HV5MXPQR2WNKJ4BTGD8CEFZ",
  "status": "passed",
  "tool_type": "figma-make",
  "policy_pack": "boilerplate",
  "created_at": "2026-03-13T15:04:18Z",
  "summary": {
    "status": "passed",
    "total_findings": 3,
    "by_severity": {
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 2,
      "info": 1
    },
    "by_dimension": {
      "token_violation": 0,
      "component_violation": 0,
      "accessibility_regression": 0,
      "design_system_drift": 2,
      "hallucinated_component": 1
    },
    "narrative": "Figma Make generated a well-structured pricing card component that correctly uses the project's approved design tokens and Tailwind utility classes throughout. No token violations or accessibility regressions were detected. Two low-severity naming convention issues and one informational observation about an unused import are noted but do not affect compliance. This output is approved for deployment."
  },
  "findings": [
    {
      "id": "finding_001",
      "severity": "LOW",
      "dimension": "design_system_drift",
      "rule": "patterns.naming-conventions",
      "file": "src/components/pricingCard.tsx",
      "line": 1,
      "code_snippet": "// File: pricingCard.tsx",
      "violation": "File uses camelCase naming. The repo convention is PascalCase for component files.",
      "expected": "File should be named PricingCard.tsx",
      "fix_suggestion": "Rename the file to PricingCard.tsx and update the import in the parent component.",
      "tool_pattern": "figma-make"
    },
    {
      "id": "finding_002",
      "severity": "LOW",
      "dimension": "design_system_drift",
      "rule": "patterns.naming-conventions",
      "file": "src/components/pricingCard.tsx",
      "line": 45,
      "code_snippet": "const handleBtnClick = () => {",
      "violation": "Handler named 'handleBtnClick' is not descriptive. Repo convention uses action-based handler names.",
      "expected": "Rename to 'handleSelectPlan' or 'handleCtaClick' to describe the action, not the element.",
      "fix_suggestion": "Rename to 'handleSelectPlan' for clarity.",
      "tool_pattern": "figma-make"
    },
    {
      "id": "finding_003",
      "severity": "INFO",
      "dimension": "hallucinated_component",
      "rule": "hallucination.unused-import",
      "file": "src/components/pricingCard.tsx",
      "line": 2,
      "code_snippet": "import { useState } from 'react'",
      "violation": "useState is imported but not used in this component. Likely a Figma Make boilerplate artifact.",
      "expected": "Remove unused imports.",
      "fix_suggestion": "Remove the useState import. If state is needed later, re-add it at that time.",
      "tool_pattern": "figma-make"
    }
  ],
  "diff_summary": {
    "files_added": ["src/components/pricingCard.tsx"],
    "files_modified": ["src/pages/Pricing.tsx"],
    "files_removed": [],
    "files_unchanged": 31,
    "baseline_commit": "b7d2e44f"
  },
  "policy_pack_version": "1.0.0",
  "aegis_version": "1.0.0"
}
```

---

## Narrative Writing Guide

The `summary.narrative` should follow this structure:

1. **What the AI did well** (1 sentence) — acknowledge the functional output
2. **Primary concern** (1 sentence) — the most important finding in plain language
3. **Secondary concern if relevant** (1 sentence, optional)
4. **Deployment verdict** (1 sentence) — "blocked", "approved with warnings", or "approved"

Keep it under 100 words. It will be read by developers and possibly by product
managers — avoid jargon. Say "hardcoded color values" not "token violations".
Say "keyboard users can't interact with the menu" not "interactive semantics regression".
