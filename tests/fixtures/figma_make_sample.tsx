/**
 * Figma Make sample fixture — known violations baked in:
 *
 * finding_001: HIGH  token_violation         — hardcoded color: '#1A1A2E' (Figma Brand/Primary Dark)
 * finding_002: HIGH  token_violation         — hardcoded color: '#4ECCA3' (Figma Accent/Teal)
 * finding_003: HIGH  token_violation         — hardcoded gap: '24px' from Figma auto-layout
 * finding_004: HIGH  accessibility_regression — <img> missing alt attribute
 * finding_005: HIGH  accessibility_regression — styled <div> used as heading (not <h1>-<h6>)
 * finding_006: LOW   design_system_drift     — component file naming: heroSection.tsx (should be HeroSection.tsx)
 *
 * Note: despite the violations, the structural layout and composition are correct.
 * This fixture should return status: blocked due to HIGH findings.
 */
import React from "react";

interface HeroSectionProps {
  title: string;
  subtitle: string;
  imageUrl: string;
  ctaLabel: string;
  onCtaClick: () => void;
}

// finding_006: This file is named heroSection.tsx in Figma Make output,
// violating the PascalCase naming convention of the source repo.
const HeroSection: React.FC<HeroSectionProps> = ({
  title,
  subtitle,
  imageUrl,
  ctaLabel,
  onCtaClick,
}) => {
  return (
    /*
     * Figma frame "Hero Container" → <div>
     * Figma auto-layout gap: 24px → hardcoded inline style
     * finding_003: gap: '24px' — should use Tailwind gap-6
     */
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        backgroundColor: "#1A1A2E",  // finding_001: Figma "Brand/Primary Dark" token
        padding: "64px 48px",
      }}
    >
      {/*
        finding_005: Figma text layer "Hero Title" styled as large text,
        but Figma Make emits a <div> instead of <h1>.
        This breaks heading hierarchy — the page has no <h1>.
      */}
      <div
        style={{
          fontSize: "48px",
          fontWeight: 700,
          color: "#4ECCA3",  // finding_002: Figma "Accent/Teal" token
          lineHeight: 1.2,
        }}
      >
        {title}
      </div>

      <p
        style={{
          fontSize: "18px",
          color: "#FFFFFF",
          maxWidth: "640px",
        }}
      >
        {subtitle}
      </p>

      {/*
        finding_004: <img> missing alt attribute.
        Figma image layers carry no alt metadata, so Figma Make omits it entirely.
      */}
      <img
        src={imageUrl}
        style={{ width: "100%", borderRadius: "12px", objectFit: "cover", height: "400px" }}
      />

      <button
        onClick={onCtaClick}
        style={{
          backgroundColor: "#4ECCA3",
          color: "#1A1A2E",
          padding: "14px 32px",
          borderRadius: "8px",
          border: "none",
          fontWeight: 600,
          cursor: "pointer",
          alignSelf: "flex-start",
        }}
      >
        {ctaLabel}
      </button>
    </div>
  );
};

export default HeroSection;
