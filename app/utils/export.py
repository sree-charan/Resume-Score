import csv
import io
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_to_csv(resumes):
    """
    Export resume analysis results to CSV format with detailed breakdowns
    """
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header row with all fields
        writer.writerow([
            # Basic Information
            'Candidate Name',
            'Email',
            'Phone',
            'Location',
            
            # Online Presence
            'LinkedIn URL',
            'GitHub URL',
            'Portfolio URL',
            'Other URLs',
            
            # Analysis Scores
            'Overall Score (%)',
            'Skills Match Score (%)',
            'Required Skills Match (%)',
            'Experience Match Score (%)',
            'Education Match Score (%)',
            'Semantic Similarity Score (%)',
            
            # Skills and Expertise
            'Technical Skills',
            'Soft Skills',
            'Languages',
            'Certifications',
            'Missing Required Skills',
            
            # Education
            'Education Level',
            'Field of Study',
            'Universities/Institutions',
            'GPA',
            'Academic Awards',
            'Graduation Years',
            
            # Work Experience
            'Years of Experience',
            'Current Position',
            'Current Company',
            'Previous Positions',
            'Companies Worked For',
            
            # Research and Publications
            'Research Papers',
            'Publications',
            'Patents',
            'Research Areas',
            
            # Projects
            'Notable Projects',
            'Project Technologies',
            'Project Links',
            
            # Leadership and Activities
            'Leadership Roles',
            'Volunteer Work',
            'Extracurricular Activities',
            
            # Personal
            'Interests/Hobbies',
            'Achievements',
            
            # Metadata
            'Original Filename',
            'Upload Date',
            'Last Updated'
        ])
        
        # Write data rows
        for resume in resumes:
            try:
                # Get detailed analysis
                analysis = resume.get_analysis()
                resume_dict = resume.to_dict()
                
                # Extract component scores
                scores = analysis['component_scores']
                skills_analysis = analysis['skills_analysis']
                
                # Helper function to format JSON lists
                def format_json_list(json_str, key=None):
                    try:
                        data = json.loads(json_str) if json_str else []
                        if key and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            return ", ".join([item.get(key, '') for item in data])
                        return ", ".join(data) if isinstance(data, list) else str(data)
                    except:
                        return ""
                
                # Write the row with all fields
                writer.writerow([
                    # Basic Information
                    resume_dict.get('candidate_name', ''),
                    resume_dict.get('email', ''),
                    resume_dict.get('phone', ''),
                    resume_dict.get('location', ''),
                    
                    # Online Presence
                    resume_dict.get('linkedin_url', ''),
                    resume_dict.get('github_url', ''),
                    resume_dict.get('portfolio_url', ''),
                    format_json_list(resume.other_urls),
                    
                    # Analysis Scores
                    f"{analysis['overall_score']:.1f}",
                    f"{scores.get('skills_match', 0):.1f}",
                    f"{scores.get('required_skills_match', 0):.1f}",
                    f"{scores.get('experience_match', 0):.1f}",
                    f"{scores.get('education_match', 0):.1f}",
                    f"{scores.get('semantic_similarity', 0):.1f}",
                    
                    # Skills and Expertise
                    format_json_list(resume.skills, 'name'),  # Assuming skills are stored as dicts with 'name' and 'level'
                    format_json_list(resume.skills),  # Soft skills
                    format_json_list(resume.languages),
                    format_json_list(resume.certifications),
                    ", ".join(skills_analysis.get('missing_skills', [])),
                    
                    # Education
                    format_json_list(resume.education, 'degree'),
                    format_json_list(resume.education, 'field'),
                    format_json_list(resume.education, 'institution'),
                    resume_dict.get('gpa', ''),
                    format_json_list(resume.academic_awards),
                    format_json_list(resume.education, 'year'),
                    
                    # Work Experience
                    resume_dict.get('total_years_experience', ''),
                    resume_dict.get('current_position', ''),
                    resume_dict.get('current_company', ''),
                    format_json_list(resume.experience, 'title'),
                    format_json_list(resume.experience, 'company'),
                    
                    # Research and Publications
                    format_json_list(resume.research_papers, 'title'),
                    format_json_list(resume.publications, 'title'),
                    format_json_list(resume.patents, 'title'),
                    format_json_list(resume.research_papers, 'area'),
                    
                    # Projects
                    format_json_list(resume.projects, 'name'),
                    format_json_list(resume.projects, 'technologies'),
                    format_json_list(resume.projects, 'url'),
                    
                    # Leadership and Activities
                    format_json_list(resume.leadership_roles),
                    format_json_list(resume.volunteer_work),
                    format_json_list(resume.extracurricular),
                    
                    # Personal
                    format_json_list(resume.interests),
                    format_json_list(resume.achievements),
                    
                    # Metadata
                    resume.original_filename,
                    resume.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    resume.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
                
            except Exception as e:
                logger.error(f"Error processing resume {resume.id}: {str(e)}")
                # Write basic info if processing fails
                writer.writerow([resume.candidate_name or "Unknown", resume.email or "", resume.phone or ""] + [""] * 40)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return "Error generating CSV export"