/**
 * Bolt.new sample fixture — known violations baked in:
 *
 * finding_001: HIGH  token_violation          — hardcoded hex in Tailwind arbitrary (bg-[#6366f1])
 * finding_002: HIGH  token_violation          — hardcoded hex in Tailwind arbitrary (text-[#f8fafc])
 * finding_003: CRITICAL hallucinated_component — lucide-react icon "Menu2" does not exist
 * finding_004: CRITICAL accessibility_regression — clickable <div> with no keyboard handler or role
 * finding_005: MEDIUM design_system_drift      — inline px spacing bypasses Tailwind scale
 */
import React, { useState } from "react";
import { Menu2, X, Home, Settings } from "lucide-react"; // Menu2 is hallucinated — it does not exist

interface NavProps {
  currentPage: string;
}

const Navbar: React.FC<NavProps> = ({ currentPage }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="w-full bg-[#6366f1] shadow-md">
      {/* finding_001: hardcoded hex color #6366f1 in Tailwind arbitrary class */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">

        <span className="text-[#f8fafc] font-bold text-lg">
          {/* finding_002: hardcoded hex color #f8fafc in Tailwind arbitrary class */}
          MyApp
        </span>

        {/* finding_004: clickable div — no role, no onKeyDown, not a <button> */}
        <div
          onClick={() => setIsOpen(!isOpen)}
          className="cursor-pointer p-2 rounded-md hover:bg-white/10"
          style={{ marginTop: "3px" }}
        >
          {/* finding_003: Menu2 does not exist in lucide-react */}
          <Menu2 size={24} className="text-white" />
        </div>
      </div>

      {isOpen && (
        <div className="bg-white border-t border-gray-100 px-4 pb-4">
          {/* finding_005: inline style spacing (marginTop: 12px) bypasses Tailwind scale */}
          <ul style={{ marginTop: "12px" }} className="space-y-1">
            <li>
              <a
                href="/"
                className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-50
                           text-gray-700 font-medium"
              >
                <Home size={16} />
                Home
              </a>
            </li>
            <li>
              <a
                href="/settings"
                className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-50
                           text-gray-700 font-medium"
              >
                <Settings size={16} />
                Settings
              </a>
            </li>
          </ul>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
