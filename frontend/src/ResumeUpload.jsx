import React, { useState } from "react";
import api from "./api";
import AnalysisModal from "./AnalysisModal";
import Mark from "./Mark";

const SUCCESS_STATUS = "Resume processed successfully using AI";

const STEPS = [
  ["Parse", "Text and skills are pulled out of the PDF."],
  ["Score", "Half the score is the range of skills found, half is how well your top matches line up."],
  ["Match", "Your skills are ranked against every job posting on file."],
];

const ResumeUpload = ({ username, onSignOut }) => {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [processingFiles, setProcessingFiles] = useState({});
  const [modalOpen, setModalOpen] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);

  // Clean filename
  const formatFileName = (name) =>
    name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9._-]/g, "");

  const rename = (list) =>
    Array.from(list).map(
      (file) => new File([file], formatFileName(file.name), { type: file.type })
    );

  // File select
  const handleFileChange = (e) => setFiles(rename(e.target.files));

  // Drag & Drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    setFiles(rename(e.dataTransfer.files));
  };

  // Poll backend until AI is done
  const waitForResumeReady = async (resumeId, interval = 2000, timeout = 300000) => {
    const start = Date.now();

    while (true) {
      const res = await api.get(`/api/resumes/${resumeId}/`);
      const status = res.data.ai_feedback?.status;

      // Any status at all is terminal — the task always writes one, success or
      // failure. Waiting only for the success string turns a failed analysis
      // into a five-minute hang.
      if (status) {
        if (status !== SUCCESS_STATUS) throw new Error(status);
        return res.data;
      }

      if (Date.now() - start > timeout) {
        throw new Error("Timed out waiting for AI processing");
      }

      await new Promise((r) => setTimeout(r, interval));
    }
  };

  const clearProcessing = (id) =>
    setProcessingFiles((prev) => {
      const updated = { ...prev };
      delete updated[id];
      return updated;
    });

  // Upload
  const handleUpload = async () => {
    if (!files.length) return setMessage("Choose a PDF first.");

    setBusy(true);
    setMessage("Uploading…");
    setProcessingFiles({});

    try {
      const uploadedResumes = [];

      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);

        const res = await api.post("/api/resumes/upload/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        const uploaded = Array.isArray(res.data.data) ? res.data.data : [res.data.data];
        uploadedResumes.push(...uploaded);

        setProcessingFiles((prev) => {
          const next = { ...prev };
          uploaded.forEach((r) => (next[r.id] = true));
          return next;
        });
      }

      setFiles([]);
      setMessage("Uploaded. Reading the document…");

      // Poll backend for each uploaded resume sequentially
      for (const r of uploadedResumes) {
        try {
          const readyResume = await waitForResumeReady(r.id);
          clearProcessing(r.id);

          setAnalysisData({
            fileName: readyResume.file.split("/").pop(),
            overallScore: readyResume.ai_feedback?.overall_score,
            skills: readyResume.ai_feedback?.skills || [],
            matches: readyResume.ai_feedback?.matches || [],
          });
          setModalOpen(true);
          setMessage("");
        } catch (err) {
          clearProcessing(r.id);
          setMessage(err.message || "The analysis did not finish. Try uploading again.");
        }
      }
    } catch (err) {
      // Surface the server's reason (file too large, not a PDF) instead of
      // sending the user to the console for it.
      const detail = err.response?.data;
      setMessage(
        detail?.errors
          ? Object.values(detail.errors).join(" ")
          : detail?.error || "Upload failed"
      );
    } finally {
      setBusy(false);
    }
  };

  const processingCount = Object.keys(processingFiles).length;

  return (
    <>
      <div className="min-h-screen">
        <header className="border-b border-rule">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
            <div className="flex items-center gap-2.5">
              <Mark className="h-6 w-6" />
              <span className="text-[15px] font-semibold tracking-tight">Resume Analyzer</span>
            </div>

            <div className="flex items-center gap-4">
              <span className="hidden font-mono text-[11px] text-muted sm:inline">
                {username}
              </span>
              <button
                onClick={onSignOut}
                className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted
                           underline decoration-rule underline-offset-4 transition-colors hover:text-stamp"
              >
                Sign out
              </button>
            </div>
          </div>
        </header>

        <main
          className="mx-auto grid max-w-6xl content-center gap-12 px-5 py-14 sm:px-8
                     lg:min-h-[calc(100vh-57px)] lg:grid-cols-[1.1fr_1fr] lg:gap-16 lg:py-16"
        >
          {/* The pitch. On a phone it sits above the sheet; the steps drop below it. */}
          <div className="animate-rise lg:col-start-1 lg:row-start-1">
            <p className="label">Resume intake</p>

            <h1 className="mt-4 max-w-[15ch] text-[2rem] font-bold leading-[1.05] tracking-[-0.03em] sm:text-[3.25rem]">
              Read your resume the way a hiring system reads it.
            </h1>

            <p className="mt-6 max-w-md text-[15px] leading-relaxed text-muted">
              Upload a PDF. You get back the skills it can actually find, a score out of 100,
              and the open postings your document ranks against.
            </p>
          </div>

          {/* The intake sheet */}
          <div
            className="animate-rise lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:self-center"
            style={{ animationDelay: "60ms" }}
          >
            <div className="sheet overflow-hidden p-6 sm:p-7">
              {/* Header band in the same stock as the report's bars. */}
              <div
                className="-mx-6 -mt-6 mb-7 flex items-baseline justify-between border-b border-rule
                           bg-bar px-6 py-3 sm:-mx-7 sm:-mt-7 sm:px-7"
              >
                <p className="label">Upload</p>
                <p className="font-mono text-[11px] text-muted">PDF · max 5 MB</p>
              </div>

              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`rounded-sheet border border-dashed p-10 text-center transition-colors
                            focus-within:border-stamp ${
                              dragging ? "border-stamp bg-bar" : "border-rule hover:bg-paper"
                            }`}
              >
                {files.length ? (
                  <ul className="space-y-2 text-left">
                    {files.map((file) => (
                      <li
                        key={file.name}
                        className="flex items-baseline justify-between gap-3 font-mono text-[12px]"
                      >
                        <span className="truncate">{file.name}</span>
                        <span className="shrink-0 text-muted">
                          {Math.max(1, Math.round(file.size / 1024))} KB
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted">Drop your resume here</p>
                )}

                <label
                  htmlFor="resume-input"
                  className="mt-4 inline-block cursor-pointer text-sm font-medium text-stamp
                             underline underline-offset-4"
                >
                  {files.length ? "Choose a different file" : "or browse files"}
                </label>

                <input
                  id="resume-input"
                  type="file"
                  accept=".pdf,application/pdf"
                  multiple
                  onChange={handleFileChange}
                  className="sr-only"
                />
              </div>

              <button onClick={handleUpload} disabled={busy} className="btn mt-6 w-full">
                {busy ? "Analyzing…" : "Analyze resume"}
              </button>

              {busy && (
                <div className="mt-5 h-px w-full overflow-hidden bg-rule" aria-hidden="true">
                  <div className="h-px w-1/4 animate-feed bg-stamp" />
                </div>
              )}

              <div role="status" aria-live="polite" className="mt-4 min-h-[1.25rem]">
                {message && <p className="font-mono text-[11px] text-muted">{message}</p>}
                {processingCount > 0 && (
                  <p className="mt-1 font-mono text-[11px] text-muted">
                    {processingCount} in the queue
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* What happens to the file, in order */}
          <ol className="max-w-md border-t border-rule lg:col-start-1 lg:row-start-2 lg:self-start">
            {STEPS.map(([name, detail], i) => (
              <li key={name} className="flex gap-5 border-b border-rule py-4">
                <span className="font-mono text-[11px] text-muted">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <p className="text-sm font-semibold tracking-tight">{name}</p>
                  <p className="mt-1 text-sm leading-relaxed text-muted">{detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </main>
      </div>

      <AnalysisModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        results={analysisData}
      />
    </>
  );
};

export default ResumeUpload;
