def job_generation_prompt(count=5):
    return f"""
Generate {count} realistic job roles.

Return JSON ONLY.
Output must be a valid JSON array.

Rules:
- Diversify industries beyond Technology or Software
- Each job must contain:
  - title (string)
  - industry (string)
  - skills (array of lowercase strings)
- Skills must be 1–3 words each
- Skills must be lowercase
- No duplicate job titles within the response

Format:
[
  {{
    "title": "backend developer",
    "industry": "software",
    "skills": ["python", "django"]
  }}
]
"""
