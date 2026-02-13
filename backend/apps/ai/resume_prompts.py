def skill_extraction_prompt(resume_text: str) -> str:
    return f"""
You are an AI that extracts professional skills from resumes.

INSTRUCTIONS:
- Extract ALL technical, software, tool, and soft skills.
- Normalize similar skills (React.js → React).
- Do NOT invent skills.
- Do NOT explain anything.
- Return STRICT JSON.
- Output MUST be a JSON object.
- Do NOT wrap in markdown.
- Do NOT include text before or after JSON.

FORMAT:
{{
  "skills": ["Skill1", "Skill2", "Skill3"]
}}

Resume:
{resume_text[:4000]}
"""
