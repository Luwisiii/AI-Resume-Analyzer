This is a web application that evaluates resumes using AI and provides instant, structured feedback on content quality, skills alignment, and overall effectiveness. It helps job seekers optimize their resumes based on intelligent analysis rather than guesswork. It uses vector embeddings and a locally hosted LLM.

The system accepts a PDF resume upload, extracts the text, analyzes it using an AI model, and returns actionable insights such as:
Resume strengths and weaknesses
Skills detected vs. missing
ATS (Applicant Tracking System) friendliness
Suggestions for improvement
Overall resume quality score

System Flow

1. **Upload**
   The user uploads a resume PDF through the React interface.

2. **Store & Extract**
   The backend built with Django saves the file and extracts the resume text.

3. **Create Embeddings**

   * Resume text → embedding vector
   * Job description → embedding vector
   * Vectors are stored in PostgreSQL using pgvector.

4. **Semantic Matching (Cosine Similarity)**
   The system computes a similarity score between the resume and job embeddings:

   ```
   resume_embedding ⋅ job_embedding
   -------------------------------- = similarity score
     ||resume|| × ||job||
   ```

   This measures **semantic meaning**, not simple keyword overlap.

5. **AI Resume Critique (Local LLM)**
   The extracted resume text is sent to Ollama running the **phi-3 mini** model.
   A structured prompt forces JSON output containing:

   * strengths
   * weaknesses
   * improvements
   * detected skills

6. **Background Processing**
   Heavy tasks (embedding, AI analysis) run asynchronously using
   Celery with Redis.

7. **Results**
   Django returns the similarity score and AI feedback to the React frontend for display.

---

How to Run the Project Locally
Prerequisites
* Python
* Node.js
* PostgreSQL (running on port **5433**)
* Redis
* Ollama installed locally
