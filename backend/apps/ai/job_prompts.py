def job_skill_extraction_prompt(descriptions, chars_per_posting: int = 600) -> str:
    """Skills for several job postings in one call.

    Postings are keyed by number rather than returned as an array so that a
    posting the model skips leaves a hole instead of shifting every later result.
    """
    listing = "\n\n".join(
        f"### {i}\n{(text or '').strip()[:chars_per_posting]}"
        for i, text in enumerate(descriptions)
    )

    return f"""
You are an AI that extracts professional skills from job postings.

INSTRUCTIONS:
- For EACH posting, extract skills a recruiter would search for: programming languages, frameworks,
  libraries, databases, tools, platforms, and established practices (e.g. CI/CD, REST APIs).
- Use the common short name, 1-3 words (e.g. "n8n", "PostgreSQL", "Docker").
- Do NOT list duties, project features, products built, or job titles
  (NOT "Sales tracking system development", "Inventory management", "Backend development").
- List each skill once; no near-duplicates ("Microservices", not also "Microservice architecture design").
- Normalize similar skills (React.js → React).
- Do NOT invent skills. A posting that names none gets an empty array.
- Do NOT explain anything.
- Return STRICT JSON.
- Output MUST be a JSON object keyed by the posting number as a string.
- Include a key for EVERY posting number below, even if its array is empty.
- Do NOT wrap in markdown.
- Do NOT include text before or after JSON.

FORMAT:
{{
  "0": ["Skill1", "Skill2"],
  "1": []
}}

Job postings:
{listing}
"""
