import React from "react";

const AnalysisModal = ({ open, onClose, results }) => {
  if (!open || !results) return null;

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-xl shadow-xl p-6 relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-black"
        >
          ✕
        </button>

        {/* Header */}
        <h2 className="text-2xl font-bold mb-1">Resume Analysis</h2>
        <p className="text-gray-500 mb-6">{results.fileName}</p>

        {/* Overall Score */}
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6 flex justify-between items-center">
          <div>
            <h3 className="font-semibold text-lg">Overall Score</h3>
            <p className="text-gray-600 text-sm">
              AI-powered resume evaluation
            </p>
          </div>
          <div className={`text-5xl font-bold ${getScoreColor(results.overallScore)}`}>
            {results.overallScore}
          </div>
        </div>

        {/* Skills */}
        {results.skills?.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold mb-2">Extracted Skills</h4>
            <div className="flex flex-wrap gap-2">
              {results.skills.map((skill, i) => (
                <span
                  key={i}
                  className="bg-gray-100 px-3 py-1 rounded-full text-sm"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Job Matches */}
        {results.matches?.length > 0 && (
          <div>
            <h4 className="font-semibold mb-3">Job Matches</h4>
            <div className="space-y-3">
              {results.matches.map((job, i) => (
                <div key={i} className="border rounded-lg p-4">
                  <div className="flex justify-between">
                    <span className="font-semibold">{job.job_title}</span>
                    <span className="text-blue-600 font-bold">
                      {job.resume_strength?.toFixed(2) || 0}%
                    </span>
                  </div>

                  {job.missing_skills?.length > 0 && (
                    <p className="text-sm text-gray-500 mt-1">
                      Missing: {job.missing_skills.join(", ")}
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
