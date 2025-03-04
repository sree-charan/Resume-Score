import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_wtf import FlaskForm
from wtforms import FileField, TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import sys

# Add parent directory to path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Initialize Flask application
app = Flask(__name__)
app.config.from_object('config')

# Import models
from app.models.resume import Resume, JobDescription
from app.utils.resume_parser import ResumeParser
from app.utils.resume_analyzer import ResumeAnalyzer
from app.utils.export import export_to_csv

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER_RESUMES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_JOB_DESCRIPTIONS'], exist_ok=True)
os.makedirs(os.path.dirname(app.config['RESUMES_JSON']), exist_ok=True)
os.makedirs(os.path.dirname(app.config['JOB_DESCRIPTIONS_JSON']), exist_ok=True)

# Form classes
class UploadForm(FlaskForm):
    resume_files = FileField('Upload Resumes', validators=[DataRequired()])
    job_description = TextAreaField('Job Description', validators=[DataRequired()])
    submit = SubmitField('Analyze')

class JobDescriptionForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    submit = SubmitField('Save')

# Routes
@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload and process resumes"""
    form = UploadForm()
    if form.validate_on_submit():
        # Save job description
        job_desc_id = str(uuid.uuid4())
        job_description_text = form.job_description.data
        job_desc_filename = f"job_desc_{job_desc_id}.txt"
        job_desc_path = os.path.join(app.config['UPLOAD_FOLDER_JOB_DESCRIPTIONS'], job_desc_filename)
        
        with open(job_desc_path, 'w', encoding='utf-8') as f:
            f.write(job_description_text)
            
        job_desc = JobDescription(
            id=job_desc_id,
            text=job_description_text,
            filename=job_desc_filename,
            path=job_desc_path,
            created_at=datetime.now().isoformat()
        )
        job_desc.save()
        
        # Process resume files
        resume_files = request.files.getlist('resume_files')
        resume_ids = []
        
        for file in resume_files:
            if file:
                # Save the resume file
                resume_id = str(uuid.uuid4())
                original_filename = secure_filename(file.filename)
                file_extension = os.path.splitext(original_filename)[1]
                resume_filename = f"resume_{resume_id}{file_extension}"
                resume_path = os.path.join(app.config['UPLOAD_FOLDER_RESUMES'], resume_filename)
                file.save(resume_path)
                
                # Parse and analyze the resume
                parser = ResumeParser(resume_path)
                parsed_data = parser.parse()
                
                analyzer = ResumeAnalyzer(parsed_data, job_description_text)
                analysis = analyzer.calculate_score()
                
                # Save to JSON storage
                resume = Resume(
                    id=resume_id,
                    original_filename=original_filename,
                    filename=resume_filename,
                    path=resume_path,
                    job_description_id=job_desc_id,
                    candidate_name=parsed_data.get('name', ''),
                    email=parsed_data.get('email', ''),
                    phone=parsed_data.get('phone', ''),
                    skills=parsed_data.get('skills', []),
                    education=parsed_data.get('education', ''),
                    experience=parsed_data.get('experience', ''),
                    score=analysis['overall_score'],
                    detailed_analysis=analysis,
                    created_at=datetime.now().isoformat()
                )
                resume.save()
                resume_ids.append(resume_id)
        
        return redirect(url_for('results', job_id=job_desc_id))
    
    return render_template('upload.html', form=form)

@app.route('/results/<job_id>')
def results(job_id):
    """Display analysis results"""
    job_description = JobDescription.get_by_id(job_id)
    if not job_description:
        flash("Job description not found", "danger")
        return redirect(url_for('index'))
        
    resume_dicts = Resume.get_by_job_id(job_id)
    resume_dicts.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Convert dictionaries to Resume objects without passing id twice
    resumes = [Resume(**r) for r in resume_dicts]
    
    return render_template('results.html', job_description=job_description, resumes=resumes)

@app.route('/resume/<resume_id>')
def view_resume(resume_id):
    """View individual resume details"""
    resume_data = Resume.get_by_id(resume_id)
    if not resume_data:
        flash("Resume not found", "danger")
        return redirect(url_for('index'))
    
    resume = Resume(**resume_data)
    return render_template('resume_detail.html', resume=resume)

@app.route('/download/<resume_id>')
def download_resume(resume_id):
    """Download original resume file"""
    resume_data = Resume.get_by_id(resume_id)
    if not resume_data:
        flash("Resume not found", "danger")
        return redirect(url_for('index'))
        
    return send_from_directory(
        os.path.dirname(resume_data['path']),
        os.path.basename(resume_data['path']),
        as_attachment=True,
        download_name=resume_data['original_filename']
    )

@app.route('/export/<job_id>')
def export_results(job_id):
    """Export analysis results to CSV"""
    job_description = JobDescription.get_by_id(job_id)
    if not job_description:
        flash("Job description not found", "danger")
        return redirect(url_for('index'))
        
    resume_dicts = Resume.get_by_job_id(job_id)
    # Convert dictionaries to Resume objects
    resumes = [Resume(**r) for r in resume_dicts]
    
    # Format data for CSV
    csv_data = export_to_csv(resumes)
    
    # Create response with CSV
    from flask import Response
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=resume_analysis_{job_id}.csv"}
    )

@app.route('/job_descriptions', methods=['GET', 'POST'])
def job_descriptions():
    """Manage job descriptions"""
    form = JobDescriptionForm()
    
    if form.validate_on_submit():
        # Save job description
        job_desc_id = str(uuid.uuid4())
        job_description_text = form.description.data
        job_desc_filename = f"job_desc_{job_desc_id}.txt"
        job_desc_path = os.path.join(app.config['UPLOAD_FOLDER_JOB_DESCRIPTIONS'], job_desc_filename)
        
        with open(job_desc_path, 'w', encoding='utf-8') as f:
            f.write(job_description_text)
            
        job_desc = JobDescription(
            id=job_desc_id,
            title=form.title.data,
            text=job_description_text,
            filename=job_desc_filename,
            path=job_desc_path,
            created_at=datetime.now().isoformat()
        )
        job_desc.save()
        
        flash("Job description saved successfully", "success")
        return redirect(url_for('job_descriptions'))
    
    job_descriptions = JobDescription.get_all()
    job_descriptions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('job_descriptions.html', form=form, job_descriptions=job_descriptions)

# Custom filters for Jinja
@app.template_filter('nl2br')
def nl2br(value):
    if value:
        return value.replace('\n', '<br>')
    return ''

@app.template_filter('format_datetime') 
def format_datetime(value, format='%Y-%m-%d'):
    """Format a datetime string"""
    if not value:
        return ''
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime(format)
    except (ValueError, TypeError):
        return value

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# For running in development mode
if __name__ == '__main__':
    app.run(debug=True)