from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def screen_resume(resume_text: str, job_description: str) -> dict:
    prompt = f"""
You are an expert HR recruiter and AI resume screener.

**Job Description:**
{job_description}

**Candidate Resume:**
{resume_text}

Analyze the resume against the job description and return a JSON with:
{{
  "match_score": <integer 0-100>,
  "skills_matched": [<list of matched skills>],
  "skills_missing": [<list of missing skills>],
  "experience_relevance": "<High/Medium/Low>",
  "education_fit": "<Good/Average/Poor>",
  "strengths": [<top 3 strengths>],
  "weaknesses": [<top 2 gaps>],
  "recommendation": "<Shortlist/Consider/Reject>",
  "summary": "<2-3 sentence overall summary>"
}}

Return ONLY valid JSON. No extra text.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)