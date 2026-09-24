import React, { useState } from "react";
import { FiChevronRight, FiFileText, FiLock, FiLogOut, FiShield, FiUploadCloud, FiX } from "react-icons/fi";
import api, { errorMessage } from "./api";
import AnalysisModal from "./AnalysisModal";
import { AnalyzeArt, InterviewArt, MatchArt, UploadArt } from "./Illustrations";
import Mark from "./Mark";
import ProgressTracker from "./ProgressTracker";

const SUCCESS_STATUS = "Resume processed successfully using AI";
const MAX_FILES = 5;
const POLL_MS = 1000;
const TIMEOUT_MS = 5 * 60 * 1000;

const HOW_IT_WORKS = [
  {
    Art: UploadArt,
    title: "Upload your resume",
    text: "Drop in a text-based PDF up to 5 MB. It's stored privately under your account.",
  },
  {
    Art: AnalyzeArt,
    title: "We read it like a hiring system",
    text: "An AI model extracts the skills it can find, then compares your experience to current postings.",
  },
  {
    Art: MatchArt,
    title: "Apply where you fit best",
    text: "Get a score out of 100, the roles you match most, and the skills each one expects that you're missing.",
  },
];

const FAQ = [
  [
    "Which files can I upload?",
    "Text-based PDFs up to 5 MB, up to 5 at a time. Scanned images of a resume have no readable text, so export your resume to PDF from Word or Google Docs instead.",
  ],
  [
    "How is my score calculated?",
    "Up to 50 points come from the range of skills found in your resume, and up to 50 from how closely your five best job matches line up with your experience.",
  ],
  [
    "Where do the job matches come from?",
    "From public job listings that are collected and refreshed on a schedule. Postings that stop appearing for 14 days are dropped, so the links you see are recent.",
  ],
  [
    "Who can see my resume?",
    "Only you. Files are never publicly linked, and every request is checked against your signed-in account.",
  ],
];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const formatFileName = (name) => name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9._-]/g, "");

const toReport = (resume) => ({
  id: resume.id,
  fileName: resume.file_name,
  overallScore: resume.ai_feedback?.overall_score ?? 0,
  skills: resume.ai_feedback?.skills || [],
  matches: resume.ai_feedback?.matches || [],
});

const ResumeUpload = ({ user, onSignOut }) => {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(null);
  const [reports, setReports] = useState([]);
  const [openReport, setOpenReport] = useState(null);

  const busy = progress !== null;

  const pick = (list) => {
    setError("");
    const pdfs = Array.from(list).filter((f) => /\.pdf$/i.test(f.name));
    if (pdfs.length < list.length) setError("Only PDF files can be analyzed.");
    if (pdfs.length > MAX_FILES) setError(`You can analyze up to ${MAX_FILES} files at a time.`);
    setFiles(
      pdfs.slice(0, MAX_FILES).map((f) => new File([f], formatFileName(f.name), { type: f.type }))
    );
  };

  // Poll until the task writes a terminal status, reporting each stage it passes.
  const waitForResult = async (resumeId) => {
    const start = Date.now();
    for (;;) {
      const { data } = await api.get(`/api/resumes/${resumeId}/`);
      const feedback = data.ai_feedback;

      if (feedback?.status) {
        if (feedback.status !== SUCCESS_STATUS) throw new Error(feedback.status);
        return data;
      }
      if (feedback?.stage) {
        // Upload + queue are the first 10%; the server's own 0–100 fills the rest.
        setProgress((p) => ({ ...p, stage: feedback.stage, percent: 10 + feedback.progress * 0.9 }));
      }
      if (Date.now() - start > TIMEOUT_MS) {
        throw new Error("This is taking longer than expected. Please try again in a few minutes.");
      }
      await sleep(POLL_MS);
    }
  };

  const handleUpload = async () => {
    if (!files.length) return setError("Choose a PDF first.");
    setError("");
    const queue = files;
    setFiles([]);

    for (const [index, file] of queue.entries()) {
      setProgress({
        fileName: file.name,
        index,
        total: queue.length,
        stage: "upload",
        percent: 0,
        startedAt: Date.now(),
      });

      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await api.post("/api/resumes/upload/", formData, {
          onUploadProgress: (e) =>
            e.total && setProgress((p) => ({ ...p, percent: (e.loaded / e.total) * 8 })),
        });
        const [uploaded] = res.data.data;

        setProgress((p) => ({ ...p, stage: "queued", percent: 10 }));
        const ready = await waitForResult(uploaded.id);

        setProgress((p) => ({ ...p, stage: "scoring", percent: 100 }));
        await sleep(400); // let the bar visibly land on 100%

        const report = toReport(ready);
        setReports((prev) => [report, ...prev]);
        if (index === queue.length - 1) setOpenReport(report);
      } catch (err) {
        setError(err.response ? errorMessage(err) : `${file.name}: ${err.message}`);
      }
    }

    setProgress(null);
  };

  const initial = (user.username || "?").charAt(0).toUpperCase();

  return (
    <>
      <div className="min-h-screen">
        {/* Top bar */}
        <header className="sticky top-0 z-40 border-b border-rule bg-paper/85 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3 sm:px-8">
            <div className="flex items-center gap-2.5">
              <Mark className="h-6 w-6" />
              <span className="text-[15px] font-semibold tracking-tight">Resume Analyzer</span>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium leading-tight">{user.username}</p>
                {user.email && <p className="text-xs text-muted">{user.email}</p>}
              </div>
              <span
                aria-hidden="true"
                className="flex h-9 w-9 items-center justify-center rounded-full bg-stamp text-sm font-semibold text-sheet"
              >
                {initial}
              </span>
              <button
                onClick={onSignOut}
                className="flex items-center gap-1.5 rounded-[10px] border border-rule px-3 py-2 text-sm text-muted transition-colors hover:border-ink hover:text-ink"
              >
                <FiLogOut aria-hidden="true" />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </div>
          </div>
        </header>

        <main>
          {/* Hero + intake */}
          <section className="mx-auto grid max-w-6xl items-center gap-10 px-5 py-12 sm:px-8 lg:grid-cols-[1fr_1.05fr] lg:gap-14 lg:py-20">
            <div className="animate-rise">
              <p className="label text-stamp">Hi {user.username} 👋</p>
              <h1 className="mt-3 text-[2.2rem] font-bold leading-[1.05] tracking-[-0.03em] sm:text-[3.1rem]">
                See your resume the way hiring software sees it.
              </h1>
              <p className="mt-5 max-w-md text-[16px] leading-relaxed text-muted">
                Upload a PDF and in a couple of minutes you'll get the skills it can find, a score
                out of 100, and the open roles you match best — each with a link to apply.
              </p>
              <ul className="mt-7 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted">
                <li className="flex items-center gap-2"><FiLock className="text-good" /> Private to your account</li>
                <li className="flex items-center gap-2"><FiShield className="text-good" /> Never shared or published</li>
              </ul>
            </div>

            <div className="animate-rise" style={{ animationDelay: "60ms" }}>
              <div className="sheet p-6 sm:p-7">
                {busy ? (
                  <ProgressTracker {...progress} />
                ) : (
                  <>
                    <div className="flex items-baseline justify-between">
                      <h2 className="text-lg font-semibold tracking-tight">Analyze a resume</h2>
                      <p className="text-xs text-muted">PDF · up to 5 MB</p>
                    </div>

                    <label
                      htmlFor="resume-input"
                      onDragOver={(e) => {
                        e.preventDefault();
                        setDragging(true);
                      }}
                      onDragLeave={() => setDragging(false)}
                      onDrop={(e) => {
                        e.preventDefault();
                        setDragging(false);
                        pick(e.dataTransfer.files);
                      }}
                      className={`mt-5 flex cursor-pointer flex-col items-center rounded-[12px] border-2 border-dashed px-6 py-10 text-center transition-colors focus-within:border-stamp ${
                        dragging ? "border-stamp bg-stamp/5" : "border-rule hover:border-stamp/50 hover:bg-paper"
                      }`}
                    >
                      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-stamp/10 text-xl text-stamp">
                        <FiUploadCloud aria-hidden="true" />
                      </span>
                      <span className="mt-4 font-medium">Drag your resume here</span>
                      <span className="mt-1 text-sm text-muted">
                        or <span className="font-semibold text-stamp underline underline-offset-4">browse your files</span>
                      </span>
                      <input
                        id="resume-input"
                        type="file"
                        accept=".pdf,application/pdf"
                        multiple
                        onChange={(e) => pick(e.target.files)}
                        className="sr-only"
                      />
                    </label>

                    {files.length > 0 && (
                      <ul className="mt-4 space-y-2">
                        {files.map((file) => (
                          <li
                            key={file.name}
                            className="flex items-center gap-3 rounded-[10px] border border-rule bg-paper px-3 py-2.5"
                          >
                            <FiFileText className="shrink-0 text-low" aria-hidden="true" />
                            <span className="min-w-0 flex-1 truncate text-sm">{file.name}</span>
                            <span className="shrink-0 font-mono text-[11px] text-muted">
                              {Math.max(1, Math.round(file.size / 1024))} KB
                            </span>
                            <button
                              onClick={() => setFiles(files.filter((f) => f !== file))}
                              aria-label={`Remove ${file.name}`}
                              className="text-muted hover:text-low"
                            >
                              <FiX />
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}

                    <button onClick={handleUpload} disabled={!files.length} className="btn mt-5 w-full">
                      Analyze {files.length > 1 ? `${files.length} resumes` : "resume"}
                    </button>
                  </>
                )}

                {error && (
                  <p role="alert" className="mt-4 rounded-[10px] border border-low/20 bg-low/5 px-3.5 py-2.5 text-sm text-low">
                    {error}
                  </p>
                )}
              </div>
            </div>
          </section>

          {/* This session's reports */}
          {reports.length > 0 && (
            <section className="mx-auto max-w-6xl px-5 pb-6 sm:px-8">
              <h2 className="text-xl font-bold tracking-tight">Your reports</h2>
              <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {reports.map((r) => (
                  <li key={r.id}>
                    <button
                      onClick={() => setOpenReport(r)}
                      className="sheet flex w-full items-center gap-4 p-4 text-left transition-colors hover:border-stamp"
                    >
                      <span className="font-mono text-2xl font-medium tabular-nums">{r.overallScore}</span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-medium">{r.fileName}</span>
                        <span className="text-xs text-muted">
                          {r.skills.length} skills · {r.matches.length} job matches
                        </span>
                      </span>
                      <FiChevronRight className="text-muted" aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* How it works */}
          <section className="border-t border-rule bg-sheet">
            <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
              <p className="label text-stamp">How it works</p>
              <h2 className="mt-2 max-w-xl text-[1.9rem] font-bold leading-tight tracking-[-0.02em]">
                From PDF to a shortlist of roles in three steps
              </h2>
              <div className="mt-10 grid gap-6 md:grid-cols-3">
                {HOW_IT_WORKS.map((step, i) => (
                  <article key={step.title} className="overflow-hidden rounded-sheet border border-rule bg-paper">
                    <step.Art className="aspect-[16/10] w-full" />
                    <div className="p-5">
                      <p className="font-mono text-[11px] text-stamp">STEP {i + 1}</p>
                      <h3 className="mt-1 text-lg font-semibold tracking-tight">{step.title}</h3>
                      <p className="mt-2 text-sm leading-relaxed text-muted">{step.text}</p>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </section>

          {/* Banner */}
          <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8">
            <div className="grid overflow-hidden rounded-sheet bg-ink md:grid-cols-[1.2fr_1fr]">
              <div className="max-w-xl self-center p-8 text-paper sm:p-12">
                <h2 className="text-[1.75rem] font-bold leading-tight tracking-[-0.02em]">
                  Walk into interviews knowing your gaps.
                </h2>
                <p className="mt-3 text-paper/80">
                  Every match lists the skills the posting asks for that your resume doesn't show yet —
                  so you know what to add, or what to prepare to talk about.
                </p>
              </div>
              <InterviewArt className="h-56 w-full md:h-full" />
            </div>
          </section>

          {/* FAQ */}
          <section className="mx-auto max-w-3xl px-5 pb-20 sm:px-8">
            <h2 className="text-center text-[1.75rem] font-bold tracking-[-0.02em]">Questions, answered</h2>
            <div className="mt-8 divide-y divide-rule rounded-sheet border border-rule bg-sheet">
              {FAQ.map(([q, a]) => (
                <details key={q} className="group px-5 py-4">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium">
                    {q}
                    <FiChevronRight className="shrink-0 text-muted transition-transform group-open:rotate-90" aria-hidden="true" />
                  </summary>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{a}</p>
                </details>
              ))}
            </div>
          </section>
        </main>

        <footer className="border-t border-rule">
          <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-5 py-6 text-xs text-muted sm:flex-row sm:px-8">
            <p className="flex items-center gap-2">
              <Mark className="h-4 w-4" /> © {new Date().getFullYear()} Resume Analyzer
            </p>
            <p>
              Your resume is private to your account. ·{" "}
              <a href="/privacy.html" className="hover:text-ink hover:underline">Privacy</a>
            </p>
          </div>
        </footer>
      </div>

      <AnalysisModal open={openReport !== null} onClose={() => setOpenReport(null)} results={openReport} />
    </>
  );
};

export default ResumeUpload;
