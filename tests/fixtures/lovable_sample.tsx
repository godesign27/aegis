/**
 * Lovable.dev sample fixture — known violations baked in:
 *
 * finding_001: HIGH     token_violation       — bg-[#F5F5F5] arbitrary color
 * finding_002: HIGH     token_violation       — text-[#333333] arbitrary color
 * finding_003: HIGH     token_violation       — border-[#E0E0E0] arbitrary color
 * finding_004: HIGH     token_violation       — text-[14px] arbitrary typography
 * finding_005: CRITICAL component_violation   — @/components/ui/button (shadcn) not installed
 * finding_006: MEDIUM   accessibility_regression — missing aria-expanded on disclosure toggle
 */
import React, { useState } from "react";
// finding_005: shadcn/ui path — component does not exist unless shadcn is set up
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ProductCardProps {
  name: string;
  price: number;
  category: string;
  inStock: boolean;
}

const ProductCard: React.FC<ProductCardProps> = ({
  name,
  price,
  category,
  inStock,
}) => {
  const [expanded, setExpanded] = useState(false);

  return (
    /* finding_001: bg-[#F5F5F5] — arbitrary hardcoded color value */
    <div className="rounded-xl bg-[#F5F5F5] p-6 shadow-sm border border-[#E0E0E0]">
      {/* finding_003: border-[#E0E0E0] — arbitrary hardcoded color value */}

      <div className="flex items-center justify-between mb-4">
        {/* finding_002: text-[#333333] — arbitrary hardcoded color value */}
        <h2 className="text-[#333333] font-semibold text-lg">{name}</h2>
        <Badge variant="outline">{category}</Badge>
      </div>

      {/* finding_004: text-[14px] — arbitrary hardcoded typography value */}
      <p className="text-[14px] text-gray-500 mb-3">
        ${price.toFixed(2)} · {inStock ? "In stock" : "Out of stock"}
      </p>

      {/*
        finding_006: disclosure button missing aria-expanded.
        The button toggles content but doesn't communicate state to assistive tech.
      */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-sm text-indigo-600 underline underline-offset-2 hover:text-indigo-800"
      >
        {expanded ? "Hide details" : "Show details"}
      </button>

      {expanded && (
        <div className="mt-3 text-sm text-gray-600 space-y-1">
          <p>SKU: PRD-{Math.random().toString(36).slice(2, 8).toUpperCase()}</p>
          <p>Ships within 2–5 business days.</p>
        </div>
      )}

      <div className="mt-4">
        <Button disabled={!inStock} className="w-full">
          {inStock ? "Add to cart" : "Notify me"}
        </Button>
      </div>
    </div>
  );
};

export default ProductCard;
