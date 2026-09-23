import React, { useEffect, useState } from "react";
import {
  FiAward,
  FiBriefcase,
  FiCheck,
  FiClock,
  FiCpu,
  FiFileText,
  FiLayers,
  FiUploadCloud,
} from "react-icons/fi";

// Keys match the stages the Celery task reports (backend/apps/resumes/tasks.py),
// plus the two the browser knows about itself: upload and queued.
const STAGES = [
  { key: "upload", label: "Upload", icon: FiUploadCloud, detail: "Sending your PDF to the server." },
  { key: "queued", label: "Queue", icon: FiClock, detail: "Waiting for an analysis worker to pick it up." },
  { key: "reading", label: "Read", icon: FiFileText, detail: "Pulling the text out of your document." },
  { key: "skills", label: "Skills", icon: FiCpu, detail: "The AI model is identifying your skills. This is usually the longest step." },
  { key: "embedding", label: "Profile", icon: FiLayers, detail: "Building a profile of your experience to compare with postings." },
  { key: "matching", label: "Match", icon: FiBriefcase, detail: "Ranking your profile against current job postings." },
  { key: "scoring", label: "Score", icon: FiAward, detail: "Putting your score together." },
];

const useElapsed = (startedAt) => {
  const [now, setNow] = useState(startedAt);
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const s = Math.max(0, Math.floor((now - startedAt) / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

const ProgressTracker = ({ fileName, index, total, stage, percent, startedAt }) => {
  const elapsed = useElapsed(startedAt);
  const current = Math.max(0, STAGES.findIndex((s) => s.key === stage));
  const active = STAGES[current];
  const value = Math.round(percent);

  return (
    <div className="animate-fade">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="label">
            Analyzing{total > 1 ? ` · file ${index + 1} of ${total}` : ""}
          </p>
          <p className="mt-1 truncate font-medium">{fileName}</p>
        </div>
        <p className="shrink-0 font-mono text-[12px] tabular-nums text-muted" aria-label="Elapsed time">
          {elapsed}
        </p>
      </div>

      {/* Percentage bar driven by the server's reported stage, not a timer. */}
      <div className="mt-5 flex items-baseline justify-between">
        <p className="text-sm font-semibold" aria-live="polite">{active.detail}</p>
        <p className="ml-4 font-mono text-2xl font-medium tabular-nums">{value}%</p>
      </div>
      <div
        role="progressbar"
        aria-label="Analysis progress"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={`${value}% — ${active.label}`}
        className="relative mt-3 h-2.5 overflow-hidden rounded-full bg-bar"
      >
        <div
          className="relative h-full overflow-hidden rounded-full bg-stamp transition-[width] duration-700 ease-out"
          style={{ width: `${Math.max(value, 2)}%` }}
        >
          <span className="absolute inset-0 animate-shine bg-gradient-to-r from-transparent via-white/35 to-transparent" />
        </div>
      </div>

      {/* Stage checklist */}
      <ol className="mt-6 grid grid-cols-7 gap-1">
        {STAGES.map(({ key, label, icon }, i) => {
          const Icon = icon;
          const done = i < current;
          const now = i === current;
          return (
            <li key={key} className="flex flex-col items-center gap-1.5 text-center">
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full border text-[13px] transition-colors ${
                  done
                    ? "border-good bg-good text-sheet"
                    : now
                    ? "border-stamp bg-stamp/10 text-stamp ring-4 ring-stamp/10"
                    : "border-rule bg-sheet text-muted"
                }`}
              >
                {done ? <FiCheck aria-hidden="true" /> : <Icon aria-hidden="true" />}
              </span>
              <span className={`text-[10.5px] leading-tight ${now ? "font-semibold text-ink" : "text-muted"}`}>
                {label}
                <span className="sr-only">{done ? " (done)" : now ? " (in progress)" : ""}</span>
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
};

export default ProgressTracker;
