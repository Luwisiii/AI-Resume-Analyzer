def skill_extraction_prompt(resume_text: str) -> str:
    return f"""
Extract ALL professional skills from this resume.

Rules:
- Include technical, practical, and soft skills
- Normalize variants (React.js → React, Node.js → Node)
- Do NOT invent skills
- Return JSON ONLY
- Skills must be concise (1–3 words)

Format:
{{
  "skills": ["React", "Python", "Leadership"]
}}

Resume:
{resume_text}
"""
