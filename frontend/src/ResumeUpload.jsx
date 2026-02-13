import React, { useState, useRef } from "react";
import axios from "axios";
import { FaFilePdf } from "react-icons/fa";
import AnalysisModal from "./AnalysisModal";

const ResumeUpload = () => {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState("");
  const [processingFiles, setProcessingFiles] = useState({});
  const [modalOpen, setModalOpen] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const dropRef = useRef(null);

  // Clean filename
  const formatFileName = (name) =>
    name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9._-]/g, "");

  // File select
  const handleFileChange = (e) => {
    const formattedFiles = Array.from(e.target.files).map(
      (file) =>
        new File([file], formatFileName(file.name), { type: file.type })
    );
    setFiles(formattedFiles);
  };

  // Drag & Drop
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

  // Poll backend until AI is done
  const waitForResumeReady = async (resumeId, interval = 2000, timeout = 300000) => {
    const start = Date.now();

    while (true) {
      try {
        const res = await axios.get(`http://127.0.0.1:8000/api/resumes/${resumeId}/`);
        const resume = res.data;

        if (resume.ai_feedback?.status === "Resume processed successfully using AI") {
          return resume;
        }
      } catch (err) {
        console.warn("Polling error:", err);
      }

      if (Date.now() - start > timeout) {
        throw new Error("Timeout waiting for AI processing");
      }

      await new Promise((r) => setTimeout(r, interval));
    }
  };

  // Upload
  const handleUpload = async () => {
    if (!files.length) return setMessage("Please select at least one file!");

    setMessage("Uploading...");
    setProcessingFiles({});

    try {
      const uploadedResumes = [];

      for (const file of files) {
        const formData = new FormData();
        formData.append("file", file);

        const res = await axios.post(
          "http://127.0.0.1:8000/api/resumes/upload/",
          formData,
          { headers: { "Content-Type": "multipart/form-data" } }
        );

        const uploaded = Array.isArray(res.data.data) ? res.data.data : [res.data.data];
        uploadedResumes.push(...uploaded);

        const processingCopy = { ...processingFiles };
        uploaded.forEach((r) => (processingCopy[r.id] = true));
        setProcessingFiles(processingCopy);
      }

      setFiles([]);
      setMessage("Files uploaded successfully! Processing with AI... ⏳");

      // 🔹 Poll backend for each uploaded resume sequentially
      for (const r of uploadedResumes) {
        try {
          const readyResume = await waitForResumeReady(r.id);

          // Remove from processing indicator
          setProcessingFiles((prev) => {
            const updated = { ...prev };
            delete updated[r.id];
            return updated;
          });

          // Update modal data and show
          setAnalysisData({
            fileName: readyResume.file.split("/").pop(),
            skills: readyResume.ai_feedback?.skills || [],
            matches: readyResume.ai_feedback?.matches || [],
          });
          setModalOpen(true);
          setMessage("");
        } catch (err) {
          console.error("Error polling resume:", err);
          setMessage("Error processing resume with AI");
        }
      }
    } catch (err) {
      console.error("Upload failed:", err);
      setMessage("Upload failed, check console");
    }
  };

  return (
    <>
      <div className="p-8 max-w-xl mx-auto bg-white shadow-xl rounded-2xl">
        <h2 className="text-2xl font-bold mb-6 text-center">Upload Your Resume</h2>

        {/* Drag & Drop Area */}
        <div
          ref={dropRef}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => dropRef.current.querySelector("input").click()}
          className="border-2 border-dashed p-8 text-center cursor-pointer rounded-xl transition hover:bg-gray-50"
        >
          {files.length ? (
            files.map((file) => (
              <div key={file.name} className="flex items-center justify-center gap-2">
                <FaFilePdf className="text-red-600" />
                <span>{file.name}</span>
              </div>
            ))
          ) : (
            <p className="text-gray-500">Drag & drop your resume here or click to select</p>
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
          className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold transition"
        >
          Analyze Resume
        </button>

        {/* Message */}
        {message && <p className="mt-4 text-center text-green-600">{message}</p>}

        {/* Processing Indicator */}
        {Object.keys(processingFiles).length > 0 && (
          <p className="text-center mt-4 text-gray-500 italic">Processing with AI… ⏳</p>
        )}
      </div>

      {/* 🔥 Analysis Modal */}
      <AnalysisModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        results={analysisData}
      />
    </>
  );
};

export default ResumeUpload;
