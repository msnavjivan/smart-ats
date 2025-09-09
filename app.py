# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import re
from collections import Counter

# Import our custom modules
from resume_parser import ResumeParser
from matching_engine import MatchingEngine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/resumes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Initialize components
resume_parser = ResumeParser()
matching_engine = MatchingEngine()

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-resume', methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
            filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Parse the resume
            try:
                parsed_data = resume_parser.parse_resume(filepath)
                
                # Save parsed data
                candidate_id = filename.replace('.', '_')
                candidate_data = {
                    'id': candidate_id,
                    'filename': filename,
                    'upload_date': datetime.now().isoformat(),
                    'parsed_data': parsed_data
                }
                
                # Save to JSON file (simulating database)
                with open(f'data/{candidate_id}.json', 'w') as f:
                    json.dump(candidate_data, f, indent=2)
                
                return jsonify({
                    'message': 'Resume uploaded and parsed successfully',
                    'candidate_id': candidate_id,
                    'parsed_data': parsed_data
                })
            except Exception as e:
                return jsonify({'error': f'Failed to parse resume: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Invalid file type'}), 400
    
    return render_template('upload_resume.html')

@app.route('/create-job', methods=['GET', 'POST'])
def create_job():
    if request.method == 'POST':
        job_data = {
            'id': f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'required_skills': [skill.strip() for skill in request.form.get('required_skills', '').split(',')],
            'experience_years': int(request.form.get('experience_years', 0)),
            'education_level': request.form.get('education_level'),
            'created_date': datetime.now().isoformat()
        }
        
        # Save job posting
        with open(f"data/{job_data['id']}.json", 'w') as f:
            json.dump(job_data, f, indent=2)
        
        return redirect(url_for('match_candidates', job_id=job_data['id']))
    
    return render_template('create_job.html')

@app.route('/match-candidates/<job_id>')
def match_candidates(job_id):
    # Load job data
    try:
        with open(f'data/{job_id}.json', 'r') as f:
            job_data = json.load(f)
    except FileNotFoundError:
        return "Job not found", 404
    
    # Load all candidates
    candidates = []
    for filename in os.listdir('data'):
        if filename.startswith('job_'):
            continue  # Skip job files
        try:
            with open(f'data/{filename}', 'r') as f:
                candidate_data = json.load(f)
                candidates.append(candidate_data)
        except:
            continue
    
    # Match candidates to job
    matches = matching_engine.match_candidates(job_data, candidates)
    
    return render_template('matches.html', job=job_data, matches=matches)

@app.route('/candidate/<candidate_id>')
def view_candidate(candidate_id):
    try:
        with open(f'data/{candidate_id}.json', 'r') as f:
            candidate_data = json.load(f)
        return render_template('candidate_details.html', candidate=candidate_data)
    except FileNotFoundError:
        return "Candidate not found", 404

@app.route('/api/suggestions/<candidate_id>')
def get_suggestions(candidate_id):
    """Get improvement suggestions for a candidate's resume"""
    try:
        with open(f'data/{candidate_id}.json', 'r') as f:
            candidate_data = json.load(f)
        
        suggestions = matching_engine.generate_suggestions(candidate_data['parsed_data'])
        return jsonify({'suggestions': suggestions})
    except FileNotFoundError:
        return jsonify({'error': 'Candidate not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)