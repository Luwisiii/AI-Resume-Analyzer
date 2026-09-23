"""Deterministic skill scan that backs up the AI extraction.

A 7B model drops skills it plainly read (TensorFlow, Python) on some runs; this list
never does. It only knows the skills below, so the AI still finds everything else.
"""
import re

# (display name, regex). Matching ignores case except inside (?-i:...), used where the
# skill is also an everyday word ("excel at", "express interest").
# ponytail: hand-kept list; extend it when a common skill keeps going missing.
KEYWORDS = [
    ("Python", r"python"),
    ("Java", r"java"),
    ("JavaScript", r"javascript|js\s*\(?es6"),
    ("TypeScript", r"typescript"),
    ("C++", r"c\+\+"),
    ("C#", r"c#"),
    ("PHP", r"php"),
    ("Ruby", r"ruby"),
    ("Kotlin", r"kotlin"),
    ("Swift", r"(?-i:Swift)"),
    ("Go", r"golang"),
    ("Rust", r"(?-i:Rust)"),
    ("SQL", r"sql"),
    ("HTML", r"html5?"),
    ("CSS", r"css3?"),
    ("React", r"react(?:\.?js)?"),
    ("React Native", r"react native"),
    ("Next.js", r"next\.?js"),
    ("Vue", r"vue(?:\.?js)?"),
    ("Angular", r"angular"),
    ("Svelte", r"svelte"),
    ("Node.js", r"node\.?\s?js"),
    ("Express", r"(?-i:Express)|express\.?js"),
    ("Django", r"django"),
    ("Flask", r"flask"),
    ("FastAPI", r"fastapi"),
    ("Laravel", r"laravel"),
    ("Spring Boot", r"spring boot"),
    (".NET", r"\.net"),
    ("Tailwind CSS", r"tailwind(?: css)?"),
    ("Bootstrap", r"bootstrap"),
    ("jQuery", r"jquery"),
    ("Redux", r"redux"),
    ("GraphQL", r"graphql"),
    ("MongoDB", r"mongodb|mongo"),
    ("MySQL", r"mysql"),
    ("PostgreSQL", r"postgres(?:ql)?"),
    ("SQLite", r"sqlite"),
    ("Redis", r"redis"),
    ("Firebase", r"firebase"),
    ("Supabase", r"supabase"),
    ("Docker", r"docker"),
    ("Kubernetes", r"kubernetes|k8s"),
    ("AWS", r"aws"),
    ("Azure", r"azure"),
    ("GCP", r"gcp|google cloud"),
    ("Git", r"git"),
    ("GitHub", r"github"),
    ("GitLab", r"gitlab"),
    ("GitHub Actions", r"github actions"),
    ("Jenkins", r"jenkins"),
    ("Linux", r"linux"),
    ("Terraform", r"terraform"),
    ("TensorFlow", r"tensorflow"),
    ("Keras", r"keras"),
    ("PyTorch", r"pytorch"),
    ("scikit-learn", r"scikit-learn|sklearn"),
    ("Pandas", r"pandas"),
    ("NumPy", r"numpy"),
    ("OpenCV", r"opencv"),
    ("CNN", r"(?-i:CNN)"),
    ("Machine Learning", r"machine learning"),
    ("Deep Learning", r"deep learning"),
    ("NLP", r"nlp|natural[- ]language processing"),
    ("Figma", r"figma"),
    ("Jest", r"jest"),
    ("Vitest", r"vitest"),
    ("Cypress", r"cypress"),
    ("Selenium", r"selenium"),
    ("Postman", r"postman"),
    ("n8n", r"n8n"),
    ("Zapier", r"zapier"),
    ("Make.com", r"make\.com"),
    ("Vercel", r"vercel"),
    ("Excel", r"(?-i:Excel)"),
    ("Power BI", r"power ?bi"),
    ("Tableau", r"tableau"),
]

# A hit may not be glued to more letters/digits ("Java" inside "JavaScript",
# "Git" inside "GitHub"); punctuation like "&" or "/" around it is fine.
_PATTERNS = [
    (name, re.compile(rf"(?<![a-z0-9])(?:{rx})(?![a-z0-9+#])", re.IGNORECASE))
    for name, rx in KEYWORDS
]


def find_skills(text):
    """Display names of every listed skill mentioned in text, in list order."""
    return [name for name, pattern in _PATTERNS if pattern.search(text)]
