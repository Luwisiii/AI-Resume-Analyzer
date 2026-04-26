import React, { useState, useRef } from "react";
import axios from "axios";
import { FaFilePdf } from "react-icons/fa";
import AnalysisModal from "./AnalysisModal";
import { DocumentMagnifyingGlassIcon } from "@heroicons/react/24/solid";
import Logo from "./assets/ai1.png";

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
    <div className="min-h-screen flex bg-gradient-to-br from-[#3b3a73] via-[#7471c6] to-[#d6d4ff] text-white">
      
      
      {/* LEFT SIDE */}
      <div className="flex-1 flex flex-col justify-center px-20">
        
        {/* Title + Icon side by side */}
        <div className="flex items-center gap-4 mb-6">
          <img
            src={Logo}
            alt="AI Resume Analyzer Logo"
            className="object-contain w-16 h-16 text-yellow-300 drop-shadow-lg  transition transform hover:scale-110"
          />
          
          <h1 className="text-6xl font-extrabold leading-tight">
            AI Resume Analyzer
          </h1>
        </div>
        
        <p className="text-lg text-gray-200 max-w-md mb-8">
          Upload your resume and let our AI analyze your skills,
          calculate your score, and match you with the best jobs instantly.
        </p>

        <button className="bg-yellow-300 text-black px-8 py-3 rounded-full font-semibold w-fit hover:scale-105 transition">
          Get Started
        </button>
      </div>
      

      {/* RIGHT SIDE */}
      <div className="flex-1 flex items-center justify-center">
        <div className="w-[420px] bg-white/10 backdrop-blur-md p-8 rounded-3xl shadow-2xl border border-white/20">

          <h2 className="text-2xl font-bold mb-6 text-center">
            Upload Resume
          </h2>

          {/* Drag & Drop */}
          <div
            ref={dropRef}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => dropRef.current.querySelector("input").click()}
            className="border-2 border-dashed border-white/40 p-8 text-center cursor-pointer rounded-2xl transition hover:bg-white/10"
          >
            {files.length ? (
              files.map((file) => (
                <div key={file.name} className="flex items-center justify-center gap-2">
                  <FaFilePdf className="text-red-400" />
                  <span>{file.name}</span>
                </div>
              ))
            ) : (
              <p className="text-gray-200">
                Drag & drop your resume here or click to select
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
            className="w-full mt-6 bg-yellow-300 text-black py-3 rounded-full font-semibold hover:scale-105 transition"
          >
            Analyze Resume
          </button>

          {message && (
            <p className="mt-4 text-center text-yellow-200">
              {message}
            </p>
          )}

          {Object.keys(processingFiles).length > 0 && (
            <p className="text-center mt-4 text-gray-300 italic">
              Processing with AI…
            </p>
          )}
        </div>
      </div>
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
