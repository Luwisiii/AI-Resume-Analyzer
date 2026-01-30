def job_generation_prompt(count=5):
    return f"""
Generate {count} job roles.

Return JSON ONLY. Avoid duplicating existing jobs in the database.

Rules:
- Include a mix of industries; try to diversify beyond Technology, IT, or Software
- Each job must have:
  - title
  - industry
  - skills (1–3 words each)
- Do NOT invent skills
- Output ONLY a JSON array

Format:
[
  {{
    "title": "Backend Developer",
    "industry": "Software",
    "skills": ["Python", "Django"]
  }}
]
"""
