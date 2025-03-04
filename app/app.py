import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_wtf import FlaskForm
from wtforms import FileField, TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import uuid
import sys

# Add parent directory to path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Initialize Flask application
app = Flask(__name__)
app.config.from_object('config')

# Initialize database and migrations
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models after db initialization to avoid circular imports
from app.models.resume import Resume, JobDescription
from app.utils.resume_parser import ResumeParser
from app.utils.resume_analyzer import ResumeAnalyzer
from app.utils.export import export_to_csv

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER_RESUMES'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_JOB_DESCRIPTIONS'], exist_ok=True)

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
            created_at=datetime.now()
        )
        db.session.add(job_desc)
        db.session.commit()
        
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
                score = analyzer.calculate_score()
                
                # Save to database
                resume = Resume(
                    id=resume_id,
                    original_filename=original_filename,
                    filename=resume_filename,
                    path=resume_path,
                    job_description_id=job_desc_id,
                    candidate_name=parsed_data.get('name', ''),
                    email=parsed_data.get('email', ''),
                    phone=parsed_data.get('phone', ''),
                    skills=','.join(parsed_data.get('skills', [])),
                    education=parsed_data.get('education', ''),
                    experience=parsed_data.get('experience', ''),
                    score=score,
                    created_at=datetime.now()
                )
                db.session.add(resume)
                resume_ids.append(resume_id)
        
        db.session.commit()
        return redirect(url_for('results', job_id=job_desc_id))
    
    return render_template('upload.html', form=form)

@app.route('/results/<job_id>')
def results(job_id):
    """Display analysis results"""
    job_description = JobDescription.query.get(job_id)
    if not job_description:
        flash("Job description not found", "danger")
        return redirect(url_for('index'))
        
    resumes = Resume.query.filter_by(job_description_id=job_id).order_by(Resume.score.desc()).all()
    return render_template('results.html', job_description=job_description, resumes=resumes)

@app.route('/resume/<resume_id>')
def view_resume(resume_id):
    """View individual resume details"""
    resume = Resume.query.get(resume_id)
    if not resume:
        flash("Resume not found", "danger")
        return redirect(url_for('index'))
        
    return render_template('resume_detail.html', resume=resume)

@app.route('/download/<resume_id>')
def download_resume(resume_id):
    """Download original resume file"""
    resume = Resume.query.get(resume_id)
    if not resume:
        flash("Resume not found", "danger")
        return redirect(url_for('index'))
        
    return send_from_directory(
        os.path.dirname(resume.path),
        os.path.basename(resume.path),
        as_attachment=True,
        download_name=resume.original_filename
    )

@app.route('/export/<job_id>')
def export_results(job_id):
    """Export analysis results to CSV"""
    job_description = JobDescription.query.get(job_id)
    if not job_description:
        flash("Job description not found", "danger")
        return redirect(url_for('index'))
        
    resumes = Resume.query.filter_by(job_description_id=job_id).order_by(Resume.score.desc()).all()
    
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
            created_at=datetime.now()
        )
        db.session.add(job_desc)
        db.session.commit()
        
        flash("Job description saved successfully", "success")
        return redirect(url_for('job_descriptions'))
    
    job_descriptions = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    return render_template('job_descriptions.html', form=form, job_descriptions=job_descriptions)

# Custom filters for Jinja
@app.template_filter('nl2br')
def nl2br(value):
    if value:
        return value.replace('\n', '<br>')
    return ''

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# For running in development mode
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)