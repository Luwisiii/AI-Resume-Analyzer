import React from "react";

/* A page with one line picked out — the product in a glyph: a document, read,
   with a single finding flagged. Replaces the stock 3D robot. */
const Mark = ({ className = "h-7 w-7" }) => (
  <svg viewBox="0 0 32 32" className={className} aria-hidden="true" focusable="false">
    <path
      d="M7 3h12l6 6v20H7z"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinejoin="round"
    />
    <path d="M19 3v6h6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    <g stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" opacity=".3">
      <path d="M11 14h10M11 22h6" />
    </g>
    <path d="M11 18h10" stroke="#1c3faa" strokeWidth="1.6" strokeLinecap="round" />
  </svg>
);

export default Mark;
