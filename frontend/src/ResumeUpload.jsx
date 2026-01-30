import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { FaFilePdf } from "react-icons/fa";

const ResumeUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [uploadProgress, setUploadProgress] = useState({});
  const [processingFiles, setProcessingFiles] = useState({});
  const dropRef = useRef(null);

  const formatFileName = (name) =>
    name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9._-]/g, "");

  const handleFileChange = (e) => {
    const formattedFiles = Array.from(e.target.files).map(
      (file) =>
        new File([file], formatFileName(file.name), { type: file.type })
    );
    setFiles(formattedFiles);
  };

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

  // Poll backend until Celery processing is done
  const waitForResumeReady = async (resumeId) => {
    let attempts = 0;

    while (attempts < 20) {
      try {
        const res = await axios.get(
          `http://127.0.0.1:8000/api/resumes/${resumeId}/`
        );

        const resume = res.data;

        // Only return if extracted_text, skills, and embedding exist
        if (
          resume.extracted_text &&
          resume.skills &&
          resume.embedding
        ) {
          return resume;
        }
      } catch (err) {
        console.warn("Polling error:", err);
      }

      await new Promise((r) => setTimeout(r, 1000));
      attempts++;
    }

    return null;
  };

  const handleUpload = async () => {
    if (!files.length) {
      setMessage("Please select at least one file!");
      return;
    }

    const uploaded = [];
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

        data.forEach((r) => (processing[r.id] = true));
        setProcessingFiles({ ...processing });

        const processed = await Promise.all(
          data.map(async (r) => {
            const readyResume = await waitForResumeReady(r.id);

            delete processing[r.id];
            setProcessingFiles({ ...processing });

            return readyResume || r;
          })
        );

        uploaded.push(...processed);
      } catch (err) {
        console.error("Upload failed:", err);
      }
    }

    setUploadedFiles(uploaded);
    setFiles([]);
    setUploadProgress({});
    setMessage("Files uploaded successfully!");
  };

  return (
    <div className="p-6 max-w-lg mx-auto bg-white shadow-lg rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Upload Your Resume(s)</h2>

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

      <button
        onClick={handleUpload}
        className="bg-blue-500 text-white px-6 py-2 rounded"
      >
        Upload
      </button>

      {message && <p className="mt-4 text-green-600">{message}</p>}

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

                {processingFiles[file.id] && (
                  <p className="text-sm italic text-gray-500">Processing… ⏳</p>
                )}

                {!processingFiles[file.id] && (
                  <>
                    {/* Safely render extracted skills */}
                    {file.skills && (
                      <p className="text-sm mt-2">
                        <strong>Extracted Skills:</strong> {file.skills}
                      </p>
                    )}

                    {/* Safely render AI feedback */}
                    {file.ai_feedback && typeof file.ai_feedback === "string" && (
                      <p className="text-sm mt-1">
                        <strong>Status:</strong> {file.ai_feedback}
                      </p>
                    )}

                    {Array.isArray(file.ai_feedback) &&
                      file.ai_feedback.length > 0 && (
                        <div className="mt-2 text-sm">
                          <strong>AI Feedback:</strong>
                          <ul className="list-disc pl-5">
                            {file.ai_feedback.map((job, idx) => (
                              <li key={idx}>
                                {job.job_title}: {job.resume_strength}%
                                {Array.isArray(job.missing_skills) &&
                                  job.missing_skills.length > 0 && (
                                    <span className="text-red-500">
                                      {" "} (Missing: {job.missing_skills.join(", ")})
                                    </span>
                                  )}
                              </li>
                            ))}
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
