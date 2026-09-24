import React from "react";

/* An R caught in a scan frame; its leg is the one finding flagged blue.
   Same drawing as public/favicon.svg. */
const Mark = ({ className = "h-7 w-7" }) => (
  <svg viewBox="0 0 32 32" className={className} aria-hidden="true" focusable="false">
    <rect width="32" height="32" rx="7" fill="#161a16" />
    <path
      d="M5.5 10.5v-5h5M21.5 5.5h5v5M26.5 21.5v5h-5M10.5 26.5h-5v-5"
      fill="none"
      stroke="#f2f4ee"
      strokeOpacity=".7"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M12.5 23V9.5h4.25a3.75 3.75 0 0 1 0 7.5H12.5"
      fill="none"
      stroke="#f2f4ee"
      strokeWidth="2.8"
      strokeLinejoin="round"
    />
    <path d="M16.5 17.5l4.25 5.5" stroke="#7d97ff" strokeWidth="3" strokeLinecap="round" />
  </svg>
);

export default Mark;
