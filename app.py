# app.py - Enhanced ATS with Better Algorithms
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import re
from collections import Counter

# Import our enhanced modules
from enhanced_resume_parser import EnhancedResumeParser
from enhanced_matching_engine import EnhancedMatchingEngine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/resumes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Initialize enhanced components
resume_parser = EnhancedResumeParser()
matching_engine = EnhancedMatchingEngine()

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_all_candidates():
    """Load all candidate data from files"""
    candidates = []
    data_dir = 'data'
    
    if not os.path.exists(data_dir):
        return candidates
    
    for filename in os.listdir(data_dir):
        if filename.startswith('job_'):
            continue  # Skip job files
        
        try:
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                candidate_data = json.load(f)
                candidates.append(candidate_data)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
    
    # Sort by upload date (newest first)
    candidates.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
    return candidates

def load_all_jobs():
    """Load all job postings from files"""
    jobs = []
    data_dir = 'data'
    
    if not os.path.exists(data_dir):
        return jobs
    
    for filename in os.listdir(data_dir):
        if not filename.startswith('job_'):
            continue  # Skip candidate files
        
        try:
            with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
                job_data = json.load(f)
                jobs.append(job_data)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
    
    # Sort by creation date (newest first)
    jobs.sort(key=lambda x: x.get('created_date', ''), reverse=True)
    return jobs

@app.route('/')
def index():
    # Load existing data
    candidates = load_all_candidates()
    jobs = load_all_jobs()
    
    return render_template('enhanced_index.html', 
                         candidates=candidates[:5],  # Show last 5 candidates
                         jobs=jobs[:5],  # Show last 5 jobs
                         total_candidates=len(candidates),
                         total_jobs=len(jobs))

@app.route('/candidates')
def view_all_candidates():
    """View all uploaded candidates"""
    candidates = load_all_candidates()
    return render_template('all_candidates.html', candidates=candidates)

@app.route('/jobs')
def view_all_jobs():
    """View all job postings"""
    jobs = load_all_jobs()
    return render_template('all_jobs.html', jobs=jobs)

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
            
            # Parse the resume with enhanced parser
            try:
                parsed_data = resume_parser.parse_resume(filepath)
                
                # Save parsed data
                candidate_id = filename.replace('.', '_')
                candidate_data = {
                    'id': candidate_id,
                    'filename': filename,
                    'original_filename': file.filename,
                    'upload_date': datetime.now().isoformat(),
                    'parsed_data': parsed_data
                }
                
                # Save to JSON file (simulating database)
                with open(f'data/{candidate_id}.json', 'w', encoding='utf-8') as f:
                    json.dump(candidate_data, f, indent=2, ensure_ascii=False)
                
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
        # Enhanced job creation with dynamic keyword extraction
        job_description = request.form.get('description', '')
        
        # Extract dynamic keywords from job description
        dynamic_keywords = matching_engine.extract_job_keywords(job_description)
        
        job_data = {
            'id': f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'title': request.form.get('title'),
            'description': job_description,
            'required_skills': [skill.strip() for skill in request.form.get('required_skills', '').split(',') if skill.strip()],
            'experience_years': int(request.form.get('experience_years', 0)),
            'education_level': request.form.get('education_level'),
            'location': request.form.get('location', ''),
            'job_type': request.form.get('job_type', 'Full-time'),
            'dynamic_keywords': dynamic_keywords,  # AI-extracted keywords
            'created_date': datetime.now().isoformat()
        }
        
        # Save job posting
        with open(f"data/{job_data['id']}.json", 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
        
        return redirect(url_for('match_candidates', job_id=job_data['id']))
    
    return render_template('enhanced_create_job.html')

@app.route('/match-candidates/<job_id>')
def match_candidates(job_id):
    # Load job data
    try:
        with open(f'data/{job_id}.json', 'r', encoding='utf-8') as f:
            job_data = json.load(f)
    except FileNotFoundError:
        return "Job not found", 404
    
    # Load all candidates
    candidates = load_all_candidates()
    
    # Enhanced matching with dynamic keywords
    matches = matching_engine.match_candidates_enhanced(job_data, candidates)
    
    return render_template('enhanced_matches.html', job=job_data, matches=matches)

@app.route('/candidate/<candidate_id>')
def view_candidate(candidate_id):
    try:
        with open(f'data/{candidate_id}.json', 'r', encoding='utf-8') as f:
            candidate_data = json.load(f)
        return render_template('candidate_detail.html', candidate=candidate_data)
    except FileNotFoundError:
        return "Candidate not found", 404

@app.route('/job/<job_id>')
def view_job(job_id):
    try:
        with open(f'data/{job_id}.json', 'r', encoding='utf-8') as f:
            job_data = json.load(f)
        return render_template('job_detail.html', job=job_data)
    except FileNotFoundError:
        return "Job not found", 404

@app.route('/api/suggestions/<candidate_id>')
def get_suggestions(candidate_id):
    """Get improvement suggestions for a candidate's resume"""
    try:
        with open(f'data/{candidate_id}.json', 'r', encoding='utf-8') as f:
            candidate_data = json.load(f)
        
        suggestions = matching_engine.generate_suggestions(candidate_data['parsed_data'])
        return jsonify({'suggestions': suggestions})
    except FileNotFoundError:
        return jsonify({'error': 'Candidate not found'}), 404

@app.route('/api/reparse/<candidate_id>')
def reparse_candidate(candidate_id):
    """Reparse a candidate with enhanced algorithms"""
    try:
        with open(f'data/{candidate_id}.json', 'r', encoding='utf-8') as f:
            candidate_data = json.load(f)
        
        # Get the original file path
        original_file = os.path.join(app.config['UPLOAD_FOLDER'], candidate_data['filename'])
        
        if not os.path.exists(original_file):
            return jsonify({'error': 'Original resume file not found'}), 404
        
        # Reparse with enhanced parser
        parsed_data = resume_parser.parse_resume(original_file)
        
        # Update candidate data
        candidate_data['parsed_data'] = parsed_data
        candidate_data['last_updated'] = datetime.now().isoformat()
        
        # Save updated data
        with open(f'data/{candidate_id}.json', 'w', encoding='utf-8') as f:
            json.dump(candidate_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'message': 'Resume reparsed successfully',
            'parsed_data': parsed_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to reparse: {str(e)}'}), 500

@app.route('/delete-candidate/<candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    """Delete a candidate and their resume file"""
    try:
        # Load candidate data to get filename
        with open(f'data/{candidate_id}.json', 'r', encoding='utf-8') as f:
            candidate_data = json.load(f)
        
        # Delete resume file
        resume_file = os.path.join(app.config['UPLOAD_FOLDER'], candidate_data['filename'])
        if os.path.exists(resume_file):
            os.remove(resume_file)
        
        # Delete data file
        data_file = f'data/{candidate_id}.json'
        if os.path.exists(data_file):
            os.remove(data_file)
        
        return jsonify({'message': 'Candidate deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete candidate: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)