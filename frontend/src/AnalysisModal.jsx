import React from "react";

/* =========================
   SCORE RING (FIXED CENTER)
   ========================= */
const ScoreRing = ({ score }) => {
  const radius = 52;
  const stroke = 10;
  const normalizedRadius = radius - stroke * 0.5;
  const circumference = normalizedRadius * 2 * Math.PI;

  const progress = Math.min(Math.max(score || 0, 0), 100);
  const strokeDashoffset =
    circumference - (progress / 100) * circumference;

  const getColor = () => {
    if (score >= 80) return "#4ade80";
    if (score >= 60) return "#facc15";
    return "#f87171";
  };

  return (
    <div className="flex items-center gap-8">

      {/* RING WRAPPER (for centering text inside) */}
      <div className="relative w-[140px] h-[140px] flex items-center justify-center">

        {/* SVG CIRCLE */}
        <svg
          height="140"
          width="140"
          className="rotate-[-90deg] absolute"
        >
          {/* Background circle */}
          <circle
            stroke="rgba(255,255,255,0.15)"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx="70"
            cy="70"
          />

          {/* Progress circle */}
          <circle
            stroke={getColor()}
            fill="transparent"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            r={normalizedRadius}
            cx="70"
            cy="70"
            style={{
              transition: "stroke-dashoffset 1.2s ease-out",
            }}
          />
        </svg>

        {/* 🔥 CENTER SCORE (FIXED) */}
        <div className="text-center z-10">
          <div className="text-3xl font-bold text-white">
            {score}
          </div>
          <div className="text-xs text-white/60">
            Score
          </div>
        </div>

      </div>

      {/* RIGHT TEXT */}
      <div>
        <h3 className="text-lg font-semibold">
          Overall Score
        </h3>
        <p className="text-white/60 text-sm">
          AI-powered resume evaluation
        </p>
      </div>

    </div>
  );
};

/* =========================
   MODAL
   ========================= */
const AnalysisModal = ({ open, onClose, results }) => {
  if (!open || !results) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 px-4">

      {/* MODAL */}
      <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto 
                      bg-white/10 backdrop-blur-md 
                      border border-white/20 
                      rounded-3xl shadow-2xl 
                      text-white p-8 relative">

        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-black/70 hover:text-yellow-300 text-xl transition"
        >
          ✕
        </button>

        {/* Header */}
        <h2 className="text-3xl font-bold mb-1">
          Resume Analysis
        </h2>
        <p className="text-white/60 mb-8">
          {results.fileName}
        </p>

        {/* SCORE RING */}
        <div className="bg-white/10 border border-white/20 rounded-2xl p-6 mb-8">
          <ScoreRing score={results.overallScore} />
        </div>

        {/* SKILLS */}
        {results.skills?.length > 0 && (
          <div className="mb-8">
            <h4 className="text-lg font-semibold mb-3">
              Extracted Skills
            </h4>

            <div className="flex flex-wrap gap-2">
              {results.skills.map((skill, i) => (
                <span
                  key={i}
                  className="bg-white/10 border border-white/20 
                             px-3 py-1 rounded-full text-sm 
                             text-white/80"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* JOB MATCHES */}
        {results.matches?.length > 0 && (
          <div>
            <h4 className="text-lg font-semibold mb-4">
              Job Matches
            </h4>

            <div className="space-y-4">
              {results.matches.map((job, i) => (
                <div
                  key={i}
                  className="bg-white/10 border border-white/20 
                             rounded-2xl p-5 
                             hover:bg-white/15 transition"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-white">
                      {job.job_title}
                    </span>

                    <span className="text-yellow-300 font-bold">
                      {job.resume_strength?.toFixed(2) || 0}%
                    </span>
                  </div>

                  {job.missing_skills?.length > 0 && (
                    <p className="text-sm text-white/60 mt-2">
                      <span className="text-white/80">
                        Missing:
                      </span>{" "}
                      {job.missing_skills.join(", ")}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default AnalysisModal;