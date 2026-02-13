import React, { useState, useRef } from "react";
import axios from "axios";
import { FaFilePdf } from "react-icons/fa";


const ResumeUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [uploadProgress, setUploadProgress] = useState({});
  const [processingFiles, setProcessingFiles] = useState({});
  const dropRef = useRef(null);

  // Helper to clean file names
  const formatFileName = (name) =>
    name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9._-]/g, "");

  // File selection
  const handleFileChange = (e) => {
    const formattedFiles = Array.from(e.target.files).map(
      (file) =>
        new File([file], formatFileName(file.name), { type: file.type })
    );
    setFiles(formattedFiles);
  };

  // Drag & drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    dropRef.current.classList.add("border-blue-400", "bg-blue-50");
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    dropRef.current.classList.remove("border-blue-400", "bg-blue-50");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    dropRef.current.classList.remove("border-blue-400", "bg-blue-50");

    const dropped = Array.from(e.dataTransfer.files).map(
      (file) =>
        new File([file], formatFileName(file.name), { type: file.type })
    );
    setFiles(dropped);
  };

  // Poll backend until AI processing is finished
  const waitForResumeReady = async (resumeId) => {
    let attempts = 0;

    while (attempts < 60) {
      try {
        const res = await axios.get(
          `http://127.0.0.1:8000/api/resumes/${resumeId}/`
        );

        const resume = res.data;

        // Check if AI processing is done
        if (
          resume.ai_feedback?.status ===
          "Resume processed successfully using AI"
        ) {
          return resume;
        }
      } catch (err) {
        console.warn("Polling error:", err);
      }

      await new Promise((r) => setTimeout(r, 2000));
      attempts++;
    }

    return null;
  };

  // Upload files
  const handleUpload = async () => {
    if (!files.length) {
      setMessage("Please select at least one file!");
      return;
    }

    setMessage("Uploading...");
    const processing = {};

    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await axios.post(
          "http://127.0.0.1:8000/api/resumes/upload/",
          formData,
          {
            headers: { "Content-Type": "multipart/form-data" },
            onUploadProgress: (e) => {
              const percent = Math.round((e.loaded * 100) / e.total);
              setUploadProgress((prev) => ({
                ...prev,
                [file.name]: percent,
              }));
            },
          }
        );

        const data = Array.isArray(res.data.data)
          ? res.data.data
          : [res.data.data];

        setUploadedFiles((prev) => [...prev, ...data]);

        // Mark as processing
        data.forEach((r) => {
          processing[r.id] = true;
        });
        setProcessingFiles({ ...processing });

        // Poll each resume
        data.forEach(async (r) => {
          const readyResume = await waitForResumeReady(r.id);

          setProcessingFiles((prev) => {
            const updated = { ...prev };
            delete updated[r.id];
            return updated;
          });

          if (readyResume) {
            setUploadedFiles((prev) =>
              prev.map((file) => (file.id === r.id ? readyResume : file))
            );
          }
        });
      } catch (err) {
        console.error("Upload failed:", err);
      }
    }

    setFiles([]);
    setUploadProgress({});
    setMessage("Files uploaded successfully!");
  };

  return (
    <div className="p-6 max-w-lg mx-auto bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Upload Your Resume(s)</h2>

      {/* Drag & Drop Area */}
      <div
        ref={dropRef}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => dropRef.current.querySelector("input").click()}
        className="border-2 border-dashed p-6 mb-4 text-center cursor-pointer rounded-lg"
      >
        {files.length ? (
          files.map((file) => (
            <div key={file.name} className="flex items-center gap-2">
              <FaFilePdf className="text-red-600" />
              <span>{file.name}</span>
            </div>
          ))
        ) : (
          <p className="text-gray-500">
            Drag & drop files here or click to select
          </p>
        )}
        <input
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />
      </div>

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        className="bg-blue-500 text-white px-6 py-2 rounded"
      >
        Upload
      </button>

      {message && <p className="mt-4 text-green-600">{message}</p>}

      {/* Uploaded Files & AI Results */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold text-lg mb-2">Uploaded Files</h3>

          <ul className="space-y-4">
            {uploadedFiles.map((file) => (
              <li key={file.id} className="border p-3 rounded">
                <div className="flex items-center gap-2">
                  <FaFilePdf className="text-red-600" />
                  <a
                    href={`http://127.0.0.1:8000${file.file}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline"
                  >
                    {file.file.split("/").pop()}
                  </a>
                </div>

                {/* Processing */}
                {processingFiles[file.id] && (
                  <p className="text-sm italic text-gray-500">
                    Processing with AI… ⏳
                  </p>
                )}

                {/* AI Feedback / Job Matches */}
                {!processingFiles[file.id] &&
                  (file.ai_feedback || file.job_feedback) && (
                    <>
                      {/* AI Feedback JSON */}
                      {file.ai_feedback && (
                        <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto mt-2">
                          {JSON.stringify(file.ai_feedback, null, 2)}
                        </pre>
                      )}

                      {/* Extracted Skills */}
                      {file.ai_feedback?.skills?.length > 0 && (
                        <p className="text-sm mt-2">
                          <strong>Extracted Skills:</strong>{" "}
                          {file.ai_feedback.skills.join(", ")}
                        </p>
                      )}

                      {/* Status */}
                      {file.ai_feedback?.status && (
                        <p className="text-sm mt-1">
                          <strong>Status:</strong> {file.ai_feedback.status}
                        </p>
                      )}

                      {/* Job Matching */}
                      {(file.ai_feedback?.matches?.length > 0 ||
                        file.job_feedback?.length > 0) && (
                        <div className="mt-2 text-sm">
                          <strong>Job Matching:</strong>
                          <ul className="list-disc pl-5">
                            {(file.ai_feedback?.matches || file.job_feedback).map(
                              (job, idx) => (
                                <li key={idx}>
                                  <span className="font-semibold">
                                    {job.job_title}
                                  </span>{" "}
                                  - {job.resume_strength?.toFixed(2) || 0}%
                                  {job.missing_skills?.length > 0 && (
                                    <span>
                                      {" "}
                                      (Missing: {job.missing_skills.join(", ")})
                                    </span>
                                  )}
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                    </>
                  )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ResumeUpload;
