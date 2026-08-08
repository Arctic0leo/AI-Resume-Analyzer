from flask import Flask, render_template, request, jsonify
import os
import re
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

app = Flask(__name__)

# -----------------------------
# Configuration
# -----------------------------

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Default skills/keywords
DEFAULT_KEYWORDS = [
    "python",
    "flask",
    "machine learning",
    "communication",
    "teamwork",
    "graphic designing",
    "adobe photoshop",
    "creativity",
    "javascript",
    "html",
    "css",
    "sql",
    "java",
    "react",
    "git",
    "github",
    "data analysis",
    "artificial intelligence",
    "ai",
]


# -----------------------------
# Helper Functions
# -----------------------------

def allowed_file(filename):
    """Check whether uploaded file is an allowed PDF."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_text_from_pdf(filepath):
    """Extract text from a PDF using PyMuPDF."""
    text = ""

    try:
        document = fitz.open(filepath)

        for page in document:
            text += page.get_text()

        document.close()

    except Exception as error:
        print(f"PDF extraction error: {error}")

    return text


def extract_keywords(text):
    """
    Extract useful words/phrases from text.
    Returns lowercase words with punctuation removed.
    """

    text = text.lower()

    # Remove punctuation
    text = re.sub(r"[^a-z0-9+#.\s-]", " ", text)

    words = text.split()

    return set(words)


def calculate_match(resume_text, jd_text):
    """
    Compare resume against job description.

    Returns:
        matched_keywords
        score
        suggestions
    """

    resume_text_lower = resume_text.lower()
    jd_text_lower = jd_text.lower()

    # First look for the default skills
    keywords = []

    for keyword in DEFAULT_KEYWORDS:
        if keyword in jd_text_lower:
            keywords.append(keyword)

    # If the job description does not contain our default keywords,
    # extract meaningful words from the job description.
    if not keywords:
        jd_words = extract_keywords(jd_text)

        # Ignore very short words
        keywords = [
            word
            for word in jd_words
            if len(word) > 3
        ]

    matched_keywords = []

    for keyword in keywords:
        if keyword in resume_text_lower:
            matched_keywords.append(keyword)

    # Calculate score
    if len(keywords) > 0:
        score = round(
            (len(matched_keywords) / len(keywords)) * 100
        )
    else:
        score = 0

    # Generate suggestions
    missing_keywords = [
        keyword
        for keyword in keywords
        if keyword not in matched_keywords
    ]

    suggestions = []

    for keyword in missing_keywords[:5]:
        suggestions.append(
            f"Consider adding '{keyword}' to your resume."
        )

    if score < 50:
        suggestions.append(
            "Try adding more skills and keywords that match the job description."
        )

    if score >= 50:
        suggestions.append(
            "Your resume contains several relevant keywords."
        )

    return matched_keywords, score, suggestions


# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    """
    Homepage.
    Flask looks for front.html inside the templates folder.
    """
    return render_template("front.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    try:

        # -------------------------
        # Check resume
        # -------------------------

        if "resume" not in request.files:
            return jsonify({
                "error": "No resume file was uploaded."
            }), 400

        resume_file = request.files["resume"]

        if resume_file.filename == "":
            return jsonify({
                "error": "Please select a resume PDF."
            }), 400

        if not allowed_file(resume_file.filename):
            return jsonify({
                "error": "Only PDF files are supported."
            }), 400

        # -------------------------
        # Get job description
        # -------------------------

        jd_text = request.form.get("jd_text", "").strip()

        if not jd_text:
            return jsonify({
                "error": "Please enter a job description."
            }), 400

        # -------------------------
        # Save uploaded PDF
        # -------------------------

        filename = secure_filename(resume_file.filename)

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        resume_file.save(filepath)

        # -------------------------
        # Extract resume text
        # -------------------------

        resume_text = extract_text_from_pdf(filepath)

        if not resume_text.strip():
            return jsonify({
                "error": "Could not extract text from the PDF."
            }), 400

        # -------------------------
        # Analyze
        # -------------------------

        matched_keywords, score, suggestions = calculate_match(
            resume_text,
            jd_text
        )

        # -------------------------
        # Delete uploaded file
        # -------------------------

        try:
            os.remove(filepath)
        except OSError:
            pass

        # -------------------------
        # Return result
        # -------------------------

        return jsonify({
            "score": score,
            "matched": matched_keywords,
            "matched_count": len(matched_keywords),
            "suggestions": suggestions
        })

    except Exception as error:

        print(f"Analysis error: {error}")

        return jsonify({
            "error": "An error occurred during resume analysis."
        }), 500


# -----------------------------
# Local Development
# -----------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
