from flask import Flask, render_template, request, jsonify
import os
import re
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Default Job Description keywords (customize as needed)
default_jd_keywords = [
    "Python", "Flask", "Machine Learning", "Communication",
    "Teamwork", "Graphic Designing", "Adobe Photoshop", "Creativity"
]

# Extract text from PDF
def extract_text_from_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Extract keywords from JD (comma-separated or line-separated phrases)
def extract_keywords(text):
    return [kw.strip() for kw in re.split(r',|\n', text) if kw.strip()]

@app.route('/')
def home():
    return render_template('front.html')  # make sure you’re using correct HTML file name

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file uploaded."}), 400

        resume_file = request.files['resume']
        jd_text = request.form.get('jdText', '')

        filename = secure_filename(resume_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(filepath)

        resume_text = extract_text_from_pdf(filepath).lower()

        jd_keywords = [kw.lower() for kw in extract_keywords(jd_text)] if jd_text.strip() else [kw.lower() for kw in default_jd_keywords]

        matched = [kw for kw in jd_keywords if kw in resume_text]
        match_percentage = int(len(matched) / len(jd_keywords) * 100)
        score = match_percentage

        suggestions = []
        for word in jd_keywords:
            if word not in matched:
                suggestions.append(f"Consider adding '{word}' to your resume.")

        suggestions.append("Use stronger action verbs in your experience section.")
        suggestions.append("Add a professional summary at the top.")

        return jsonify({
            "score": score,
            "match": f"{len(matched)} of {len(jd_keywords)} matched",
            "suggestions": suggestions
        })
    
    except Exception as e:
        print("ERROR during analysis:", e)
        return jsonify({"error": "An error occurred during resume analysis."}), 500

if __name__ == '__main__':
    app.run(debug=True)
