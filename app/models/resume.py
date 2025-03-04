from app.app import db
from datetime import datetime
from app.utils.resume_analyzer import ResumeAnalyzer
import json

class Resume(db.Model):
    """Model for storing resume information and analysis results"""
    __tablename__ = 'resumes'
    
    id = db.Column(db.String(36), primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    job_description_id = db.Column(db.String(36), db.ForeignKey('job_descriptions.id'), nullable=False)
    
    # Basic Information
    candidate_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    location = db.Column(db.String(255))
    
    # Online Presence
    linkedin_url = db.Column(db.String(255))
    github_url = db.Column(db.String(255))
    portfolio_url = db.Column(db.String(255))
    other_urls = db.Column(db.Text)  # JSON list of other relevant URLs
    
    # Skills and Expertise
    skills = db.Column(db.Text)  # JSON list of skills with proficiency levels
    languages = db.Column(db.Text)  # JSON list of languages with proficiency
    certifications = db.Column(db.Text)  # JSON list of certifications
    
    # Education
    education = db.Column(db.Text)  # JSON array of education history
    gpa = db.Column(db.Float)
    academic_awards = db.Column(db.Text)  # JSON list of academic achievements
    
    # Work Experience
    experience = db.Column(db.Text)  # JSON array of work experience
    total_years_experience = db.Column(db.Float)
    current_position = db.Column(db.String(255))
    current_company = db.Column(db.String(255))
    
    # Research and Publications
    research_papers = db.Column(db.Text)  # JSON array of research papers
    publications = db.Column(db.Text)  # JSON array of other publications
    patents = db.Column(db.Text)  # JSON array of patents
    
    # Projects
    projects = db.Column(db.Text)  # JSON array of projects
    
    # Leadership and Activities
    leadership_roles = db.Column(db.Text)  # JSON array of leadership positions
    volunteer_work = db.Column(db.Text)  # JSON array of volunteer experience
    extracurricular = db.Column(db.Text)  # JSON array of activities
    
    # Personal
    interests = db.Column(db.Text)  # JSON list of interests/hobbies
    achievements = db.Column(db.Text)  # JSON list of personal achievements
    
    # Analysis results
    score = db.Column(db.Float, default=0.0)
    detailed_analysis = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    job_description = db.relationship('JobDescription', backref=db.backref('resumes', lazy=True))
    
    def __repr__(self):
        return f"<Resume {self.id} - {self.candidate_name}>"
    
    def get_skills_list(self):
        """Convert skills string to list"""
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',')]
        return []
    
    def get_analysis(self, reanalyze=False):
        """
        Get detailed analysis results for the resume.
        If reanalyze is True or no analysis exists, perform a new analysis.
        
        Returns:
            dict: Detailed analysis results
        """
        if not reanalyze and self.detailed_analysis:
            try:
                return json.loads(self.detailed_analysis)
            except:
                pass
        
        # Create resume data dict for analyzer
        resume_data = {
            'name': self.candidate_name,
            'email': self.email,
            'phone': self.phone,
            'skills': self.get_skills_list(),
            'education': self.education,
            'experience': self.experience
        }
        
        # Perform analysis
        analyzer = ResumeAnalyzer(resume_data, self.job_description.text)
        analysis_results = analyzer.calculate_score()
        
        # Store results
        self.detailed_analysis = json.dumps(analysis_results)
        self.score = analysis_results['overall_score']
        db.session.commit()
        
        return analysis_results

    def to_dict(self):
        """Convert resume to dictionary format"""
        return {
            'id': self.id,
            'candidate_name': self.candidate_name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'linkedin_url': self.linkedin_url,
            'github_url': self.github_url,
            'portfolio_url': self.portfolio_url,
            'other_urls': json.loads(self.other_urls) if self.other_urls else [],
            'skills': json.loads(self.skills) if self.skills else [],
            'languages': json.loads(self.languages) if self.languages else [],
            'certifications': json.loads(self.certifications) if self.certifications else [],
            'education': json.loads(self.education) if self.education else [],
            'gpa': self.gpa,
            'academic_awards': json.loads(self.academic_awards) if self.academic_awards else [],
            'experience': json.loads(self.experience) if self.experience else [],
            'total_years_experience': self.total_years_experience,
            'current_position': self.current_position,
            'current_company': self.current_company,
            'research_papers': json.loads(self.research_papers) if self.research_papers else [],
            'publications': json.loads(self.publications) if self.publications else [],
            'patents': json.loads(self.patents) if self.patents else [],
            'projects': json.loads(self.projects) if self.projects else [],
            'leadership_roles': json.loads(self.leadership_roles) if self.leadership_roles else [],
            'volunteer_work': json.loads(self.volunteer_work) if self.volunteer_work else [],
            'extracurricular': json.loads(self.extracurricular) if self.extracurricular else [],
            'interests': json.loads(self.interests) if self.interests else [],
            'achievements': json.loads(self.achievements) if self.achievements else [],
            'score': self.score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class JobDescription(db.Model):
    """Model for storing job descriptions"""
    __tablename__ = 'job_descriptions'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255))
    text = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        if self.title:
            return f"<JobDescription {self.id} - {self.title}>"
        return f"<JobDescription {self.id}>"