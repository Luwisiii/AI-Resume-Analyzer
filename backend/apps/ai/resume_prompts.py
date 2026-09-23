def skill_extraction_prompt(resume_text: str) -> str:
    return f"""
You are an AI that extracts professional skills from resumes.

INSTRUCTIONS:
- Extract skills a recruiter would search for: programming languages, frameworks,
  libraries, databases, tools, platforms, and established practices (e.g. CI/CD, REST APIs).
- Use the common short name, 1-3 words (e.g. "n8n", "PostgreSQL", "Docker").
- Be complete: include every such skill named ANYWHERE in the resume — summary,
  experience, projects, and tools sections alike.
- Do NOT list duties, project features, products built, or job titles
  (NOT "Sales tracking system development", "Inventory management", "Backend development").
- List each skill once; no near-duplicates ("Microservices", not also "Microservice architecture design").
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
