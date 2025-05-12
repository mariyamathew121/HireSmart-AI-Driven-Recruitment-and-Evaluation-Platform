import os
import re
import nltk
import ast
from io import BytesIO
from bson.objectid import ObjectId
import json

from flask import Flask, request, jsonify
from pymongo import MongoClient
from gridfs import GridFS

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import PyPDF2

# ─── Setup ─────────────────────────────────────────────────────────────────────

nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

app = Flask(__name__)
@app.route("/")
def home():
    return "Resume Screening App is running!"

if __name__ == "__main__":
    app.run(debug=True, port=5002)
    
# Gemini AI setup
genai.configure(api_key="AIzaSyqT3Q274")
gemini = genai.GenerativeModel("gemini-1.5-flash")

# Sentence-BERT for semantic similarity
sbert = SentenceTransformer('all-MiniLM-L6-v2')

# NLTK tools
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# MongoDB + GridFS
client = MongoClient("mongodb://localhost:27017/")
db = client["HireSmart"]
fs = GridFS(db)
jobs_collection       = db["Jobs"]
applicants_collection = db["Applicant"]
results_collection    = db["Results"]

# Optional: Insert sample data
if jobs_collection.count_documents({}) == 0:
    jobs_collection.insert_one({"title": "Software Engineer", "requirements": ["Python", "MongoDB"]})

if applicants_collection.count_documents({}) == 0:
    applicants_collection.insert_one({"name": "John Doe", "skills": ["Python", "Django"]})

print("Database and collections ready.")

# ─── Utility Functions ─────────────────────────────────────────────────────────

def extract_text_from_pdf(stream: BytesIO) -> str:
    reader = PyPDF2.PdfReader(stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    tokens = [w for w in text.split() if w not in stop_words]
    return ' '.join(lemmatizer.lemmatize(w) for w in tokens)

def replace_shortforms(text: str, sf: dict) -> str:
    for short, full in sf.items():
        text = re.sub(rf'\b{re.escape(short)}\b', full, text)
    return text

def semantic_task(jd: str, res: str) -> float:
    emb_j = sbert.encode([jd])
    emb_r = sbert.encode([res])
    return float(cosine_similarity(emb_j, emb_r)[0][0])

def ner_task(prompt: str) -> str:
    return gemini.generate_content(prompt).text

def compute_skill_similarity(jd_skills, res_skills):
    if not jd_skills or not res_skills:
        return 0.0
    vec = CountVectorizer(stop_words='english')
    m = vec.fit_transform([' '.join(jd_skills), ' '.join(res_skills)])
    return float(cosine_similarity(m[0], m[1])[0][0])

# ─── Main Endpoint ─────────────────────────────────────────────────────────────

@app.route('/process', methods=['POST'])
def process_data():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    job_id  = data.get('job_id')
    if not user_id or not job_id:
        return jsonify(error="Missing user_id or job_id"), 400

    # 1. Fetch job description
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job or not job.get('jobDescription'):
        return jsonify(error="Job not found or missing description"), 404
    jd_raw = job['jobDescription']

    # 2. Fetch applicant & resume
    appl = applicants_collection.find_one({"_id": ObjectId(user_id)})
    if not appl or 'education' not in appl or not appl['education'].get('resume_file_id'):
        return jsonify(error="Applicant or resume not found"), 404
    rf_id = appl['education']['resume_file_id']
    pdf_bytes = fs.get(ObjectId(rf_id)).read()
    resume_raw = extract_text_from_pdf(BytesIO(pdf_bytes))
    
    import ast
    import re

    def extract_python_dict(gemini_response):
        # Remove Markdown code block if present
        cleaned = re.sub(r"```(?:python)?\s*", "", gemini_response)
        cleaned = re.sub(r"\s*```", "", cleaned)
        return ast.literal_eval(cleaned)
    # 3. Load shortform dictionary
    sf_path = data.get('shortform_file_path', 'shortform.txt')
    sf_dict = {}
    if os.path.exists(sf_path):
        with open(sf_path) as f:
            for line in f:
                if ':' in line:
                    k, v = line.strip().split(':', 1)
                    sf_dict[k.strip()] = v.strip()

    # 4. Clean & expand texts
    jd_clean = replace_shortforms(preprocess(jd_raw), sf_dict)
    res_clean = replace_shortforms(preprocess(resume_raw), sf_dict)

    # 5. Prompts to Gemini – expects actual Python arrays
    system_prompt_job = f"""
You are a Python data extractor.

Your task:
- Extract and return two Python lists: one for EXPERIENCE and one for SKILL.
- Return them inside a single Python dictionary using this format:

{{
    "jd_experience": ["experience1", "experience2", ...],
    "jd_skill": ["skill1", "skill2", ...]
}}

Only return valid Python dictionary code. No explanations. No JSON. No markdown. No comments. Only Python dict.

Input job description:
{jd_clean}
"""

    system_prompt_resume = f"""
You are a Python data extractor.

Your task:
- Extract and return three Python lists:
    - res_experience: list of experience strings
    - res_skill: list of skill strings
    - res_project: list of project strings

Return them inside a Python dictionary using this format:

{{
    "res_experience": ["exp1", "exp2", ...],
    "res_skill": ["skill1", "skill2", ...],
    "res_project": ["project1", "project2", ...]
}}

Only return valid Python dictionary code. No explanations. No JSON. No markdown. No comments. Only Python dict.

Input resume text:
{res_clean}
"""

    # 6. Run tasks sequentially
    sem_score = semantic_task(jd_clean, res_clean)

    jd_ner_python  = ner_task(system_prompt_job)
    res_ner_python = ner_task(system_prompt_resume)

    # Safely parse the response using ast.literal_eval
    jd_ner_dict  = extract_python_dict(jd_ner_python)
    res_ner_dict = extract_python_dict(res_ner_python)


    # Step 2: Extract arrays
    jd_experience = jd_ner_dict.get("jd_experience", [])
    jd_skill      = jd_ner_dict.get("jd_skill", [])

    res_experience = res_ner_dict.get("res_experience", [])
    res_skill      = res_ner_dict.get("res_skill", [])
    res_project    = res_ner_dict.get("res_project", [])

    # Debug prints
    print("Job Description Experience:", jd_experience)
    print("Job Description Skills:", jd_skill)
    print("Resume Experience:", res_experience)
    print("Resume Skills:", res_skill)
    print("Resume Projects:", res_project)

    # 8. Counts
    exp_count  = len(res_experience)
    proj_count = len(res_project)

    # 9. Compute scores
    # Normalize skill similarity & semantic similarity (already between 0 and 1)
    skl_sim = compute_skill_similarity(jd_skill, res_skill)
    sem_score = min(1.0, sem_score)

    # Normalize counts
    exp_score_raw = min(5, exp_count) / 5   # max 5 points
    proj_score_raw = min(3, proj_count) / 3 # max 3 points

    # Optional: rule-based overlap score (Jaccard-like)
    def skill_overlap(jd, res):
        jd_set = set([s.lower() for s in jd])
        res_set = set([s.lower() for s in res])
        if not jd_set:
            return 0.0
        return len(jd_set & res_set) / len(jd_set)

    overlap_score = skill_overlap(jd_skill, res_skill)

    # Hybrid weighted scoring
    weighted_score = (
        0.40 * sem_score +
        0.25 * skl_sim +
        0.15 * exp_score_raw +
        0.10 * proj_score_raw +
        0.10 * overlap_score
    )


    # 10. Persist results
    results_collection.insert_one({
    "user_id": user_id,
    "job_id": job_id,
    "semantic_score": sem_score,
    "jd_experience_entities": jd_experience,
    "jd_skill_entities": jd_skill,
    "resume_experience_entities": res_experience,
    "resume_project_entities":   res_project,
    "resume_skill_entities":     res_skill,
    "experience_count": exp_count,
    "project_count": proj_count,
    "experience_score": exp_score_raw,
    "project_score": proj_score_raw,
    "skill_similarity": skl_sim,
    "skill_overlap_score": overlap_score,
    "total_score": (weighted_score / 3.0) * 100
})
    # 11. Return response
    return jsonify({
    "semantic_score": sem_score,
    "experience_score": exp_score_raw,
    "project_score": proj_score_raw,
    "skill_similarity": skl_sim,
    "skill_overlap_score": overlap_score,
    "total_score": (weighted_score / 3.0) * 100
}), 200

if __name__ == '__main__':
    app.run(port=5002, debug=True)
