from datetime import datetime
import json
import os
import numpy as np
from app.utils.resume_analyzer import ResumeAnalyzer
from config import RESUMES_JSON, JOB_DESCRIPTIONS_JSON

class NumpyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def load_json_file(filepath):
    """Load data from JSON file, create if doesn't exist or is corrupted"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    # If file is corrupted, backup the file and return empty list
                    backup_path = filepath + '.bak'
                    os.rename(filepath, backup_path)
                    return []
    except Exception as e:
        print(f"Error loading JSON file {filepath}: {str(e)}")
        return []
        
    # Create new file if doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump([], f)
    return []

def save_json_file(filepath, data):
    """Save data to JSON file using custom encoder for numpy types"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, cls=NumpyJSONEncoder)

class Resume:
    """Class for managing resume information and analysis results"""
    
    @staticmethod
    def get_all():
        """Get all resumes"""
        return load_json_file(RESUMES_JSON)
    
    @staticmethod
    def get_by_id(id):
        """Get resume by ID"""
        resumes = load_json_file(RESUMES_JSON)
        return next((r for r in resumes if r['id'] == id), None)
    
    @staticmethod
    def get_by_job_id(job_id):
        """Get all resumes for a job description"""
        resumes = load_json_file(RESUMES_JSON)
        return [r for r in resumes if r['job_description_id'] == job_id]
    
    def __init__(self, id=None, **kwargs):
        if id is None and 'id' in kwargs:
            id = kwargs.pop('id')
        self.id = id
        self.data = kwargs
        self._job_description = None  # Cache for job description
        
    @property
    def job_description(self):
        """Get the associated job description object"""
        if self._job_description is None and self.data.get('job_description_id'):
            job_data = JobDescription.get_by_id(self.data['job_description_id'])
            if job_data:
                self._job_description = JobDescription(**job_data)
        return self._job_description
        
    def __getattr__(self, name):
        """Allow accessing data dict values as attributes"""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'Resume' object has no attribute '{name}'")
        
    def __dir__(self):
        """List available attributes for autocompletion"""
        return super().__dir__() + list(self.data.keys())
        
    def save(self):
        """Save resume to JSON storage"""
        resumes = load_json_file(RESUMES_JSON)
        
        # Update existing or add new
        self.data['id'] = self.id
        existing_idx = next((i for i, r in enumerate(resumes) if r['id'] == self.id), None)
        
        if existing_idx is not None:
            resumes[existing_idx] = self.data
        else:
            resumes.append(self.data)
        
        save_json_file(RESUMES_JSON, resumes)
    
    def get_analysis(self, reanalyze=False):
        """Get detailed analysis results for the resume"""
        if not reanalyze and self.data.get('detailed_analysis'):
            return self.data['detailed_analysis']
        
        # Create resume data dict for analyzer
        resume_data = {
            'name': self.data.get('candidate_name'),
            'email': self.data.get('email'),
            'phone': self.data.get('phone'),
            'skills': self.get_skills_list(),
            'education': self.data.get('education'),
            'experience': self.data.get('experience')
        }
        
        # Get job description
        job_desc = JobDescription.get_by_id(self.data['job_description_id'])
        
        # Perform analysis
        analyzer = ResumeAnalyzer(resume_data, job_desc['text'])
        analysis_results = analyzer.calculate_score()
        
        # Store results
        self.data['detailed_analysis'] = analysis_results
        self.data['score'] = analysis_results['overall_score']
        self.save()
        
        return analysis_results
    
    def get_skills_list(self):
        """Convert skills string to list"""
        skills = self.data.get('skills', '')
        if isinstance(skills, list):
            return skills
        return [skill.strip() for skill in skills.split(',')] if skills else []

class JobDescription:
    """Class for managing job descriptions"""
    
    @staticmethod
    def get_all():
        """Get all job descriptions"""
        return load_json_file(JOB_DESCRIPTIONS_JSON)
    
    @staticmethod
    def get_by_id(id):
        """Get job description by ID"""
        jobs = load_json_file(JOB_DESCRIPTIONS_JSON)
        return next((j for j in jobs if j['id'] == id), None)
    
    def __init__(self, id=None, **kwargs):
        if id is None and 'id' in kwargs:
            id = kwargs.pop('id')
        self.id = id
        self.data = kwargs
        
    def __getattr__(self, name):
        """Allow accessing data dict values as attributes"""
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'JobDescription' object has no attribute '{name}'")
        
    def __dir__(self):
        """List available attributes for autocompletion"""
        return super().__dir__() + list(self.data.keys())
        
    def save(self):
        """Save job description to JSON storage"""
        jobs = load_json_file(JOB_DESCRIPTIONS_JSON)
        
        # Update existing or add new
        self.data['id'] = self.id
        existing_idx = next((i for i, j in enumerate(jobs) if j['id'] == self.id), None)
        
        if existing_idx is not None:
            jobs[existing_idx] = self.data
        else:
            jobs.append(self.data)
        
        save_json_file(JOB_DESCRIPTIONS_JSON, jobs)