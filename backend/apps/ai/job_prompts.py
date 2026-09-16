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
- Extract ALL technical, software, tool, and soft skills for EACH posting.
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
