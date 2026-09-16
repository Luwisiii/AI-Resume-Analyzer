import React, { useEffect } from "react";

/* How recently a fetch last confirmed the posting is still listed. Shown so a
   candidate can judge a link rather than assume every one is live. */
const seenAgo = (iso) => {
  if (!iso) return null;
  const days = Math.floor((Date.now() - new Date(iso)) / 86400000);
  if (Number.isNaN(days)) return null;
  if (days <= 0) return "seen today";
  if (days === 1) return "seen yesterday";
  return `seen ${days} days ago`;
};

const SEGMENTS = 20;

const band = (score) => {
  if (score >= 80) return { text: "Strong", color: "#1e6b3d" };
  if (score >= 60) return { text: "Moderate", color: "#8a6412" };
  return { text: "Needs work", color: "#a4352a" };
};

/* A printed gauge, not a dial: twenty ticks, five points each, filling left to
   right the way a meter on a report would. */
const Meter = ({ score }) => {
  const value = Math.min(Math.max(score || 0, 0), 100);
  const filled = Math.round((value / 100) * SEGMENTS);
  const { color } = band(value);

  return (
    <div
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Overall score"
      className="flex h-6 gap-[3px]"
    >
      {Array.from({ length: SEGMENTS }, (_, i) => (
        <span
          key={i}
          className="flex-1 animate-fade rounded-[1px]"
          style={{
            animationDelay: `${i * 20}ms`,
            backgroundColor: i < filled ? color : "#e5eee1",
          }}
        />
      ))}
    </div>
  );
};

const AnalysisModal = ({ open, onClose, results }) => {
  useEffect(() => {
    if (!open) return;

    const onKey = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open || !results) return null;

  const score = results.overallScore ?? 0;
  const skills = results.skills || [];
  const matches = results.matches || [];

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-ink/45 px-4 py-8 sm:px-6"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="report-title"
        onClick={(e) => e.stopPropagation()}
        className="sheet perf mx-auto w-full max-w-3xl animate-rise"
      >
        <div className="px-9 py-9 sm:px-12 sm:py-10">
          {/* Masthead */}
          <div className="flex items-start justify-between gap-6 border-b border-rule pb-5">
            <div className="min-w-0">
              <p className="label">Analysis report</p>
              <h2
                id="report-title"
                className="mt-2 truncate font-mono text-[15px] font-medium text-ink"
              >
                {results.fileName}
              </h2>
            </div>

            <button
              onClick={onClose}
              aria-label="Close report"
              className="-mt-1 shrink-0 rounded-sheet border border-rule px-2.5 py-1
                         font-mono text-[11px] text-muted transition-colors
                         hover:border-ink hover:text-ink"
            >
              Close
            </button>
          </div>

          {/* Score */}
          <div className="flex flex-col gap-8 border-b border-rule py-9 sm:flex-row sm:items-end">
            <div className="shrink-0">
              <div className="font-mono text-[64px] font-medium leading-none tracking-tight tabular-nums">
                {score}
                <span className="ml-1 align-top text-base text-muted">/100</span>
              </div>
              <p
                className="mt-3 font-mono text-[11px] font-medium uppercase tracking-[0.16em]"
                style={{ color: band(score).color }}
              >
                {band(score).text}
              </p>
            </div>

            <div className="min-w-0 flex-1">
              <Meter score={score} />
              <p className="mt-3 text-sm leading-relaxed text-muted">
                Up to 50 points for the range of skills found in the document, up to 50 for
                how strongly your top matches line up.
              </p>
            </div>
          </div>

          {/* Skills */}
          <div className="border-b border-rule py-8">
            <div className="flex items-baseline justify-between">
              <p className="label">Skills found</p>
              <p className="font-mono text-[11px] text-muted">{skills.length}</p>
            </div>

            {skills.length ? (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {skills.map((skill, i) => (
                  <span
                    key={i}
                    className="rounded-sheet border border-rule bg-bar px-2.5 py-1 font-mono text-[11px]"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-muted">
                No skills were readable in this file. A text-based PDF, rather than a scan,
                gives the parser something to work with.
              </p>
            )}
          </div>

          {/* Matches — greenbar */}
          <div className="pt-8">
            <div className="flex items-baseline justify-between">
              <p className="label">Job matches</p>
              <p className="font-mono text-[11px] text-muted">{matches.length}</p>
            </div>

            {matches.length ? (
              <div className="-mx-4 mt-5 sm:-mx-7">
                {matches.map((job, i) => (
                  <div
                    key={i}
                    className={`px-4 py-5 sm:px-7 ${i % 2 === 0 ? "bg-bar" : "bg-sheet"}`}
                  >
                    <div className="flex items-baseline justify-between gap-6">
                      <div className="min-w-0">
                        <p className="font-semibold tracking-tight">{job.job_title}</p>

                        {(job.company || job.location) && (
                          <p className="mt-0.5 truncate text-sm text-muted">
                            {[job.company, job.location].filter(Boolean).join(" · ")}
                          </p>
                        )}
                      </div>

                      <span className="shrink-0 font-mono text-sm font-medium tabular-nums">
                        {(job.resume_strength ?? 0).toFixed(1)}%
                      </span>
                    </div>

                    {job.missing_skills?.length > 0 && (
                      <p className="mt-3 text-sm leading-relaxed text-muted">
                        <span className="label">Missing</span>{" "}
                        {job.missing_skills.join(", ")}
                      </p>
                    )}

                    {job.url && (
                      <div className="mt-3 flex flex-wrap items-baseline gap-4">
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-stamp underline underline-offset-4"
                        >
                          Open posting ↗
                        </a>

                        {seenAgo(job.last_seen) && (
                          <span className="font-mono text-[11px] text-muted">
                            {seenAgo(job.last_seen)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm leading-relaxed text-muted">
                Nothing on file clears the match threshold yet. New postings are collected on
                a schedule — upload again once more have landed.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisModal;
