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
                # Get data from resume object
                data = resume.data
                # Get detailed analysis
                analysis = data.get('detailed_analysis', {})
                scores = analysis.get('component_scores', {})
                skills_analysis = analysis.get('skills_analysis', {})
                
                # Helper function to format list data
                def format_list(data):
                    if isinstance(data, list):
                        return ", ".join(str(item) for item in data)
                    elif isinstance(data, str):
                        return data
                    return ""
                
                # Write the row with all fields
                writer.writerow([
                    # Basic Information
                    data.get('candidate_name', ''),
                    data.get('email', ''),
                    data.get('phone', ''),
                    data.get('location', ''),
                    
                    # Online Presence
                    data.get('linkedin_url', ''),
                    data.get('github_url', ''),
                    data.get('portfolio_url', ''),
                    format_list(data.get('other_urls', [])),
                    
                    # Analysis Scores
                    f"{data.get('score', 0):.1f}",
                    f"{scores.get('skills_match', 0):.1f}",
                    f"{scores.get('required_skills_match', 0):.1f}",
                    f"{scores.get('experience_match', 0):.1f}",
                    f"{scores.get('education_match', 0):.1f}",
                    f"{scores.get('semantic_similarity', 0):.1f}",
                    
                    # Skills and Expertise
                    format_list(resume.get_skills_list()),  # Use get_skills_list() method
                    format_list(data.get('soft_skills', [])),
                    format_list(data.get('languages', [])),
                    format_list(data.get('certifications', [])),
                    format_list(skills_analysis.get('missing_skills', [])),
                    
                    # Education
                    data.get('education_level', ''),
                    data.get('field_of_study', ''),
                    data.get('universities', ''),
                    data.get('gpa', ''),
                    format_list(data.get('academic_awards', [])),
                    data.get('graduation_years', ''),
                    
                    # Work Experience
                    data.get('total_years_experience', ''),
                    data.get('current_position', ''),
                    data.get('current_company', ''),
                    format_list(data.get('previous_positions', [])),
                    format_list(data.get('companies', [])),
                    
                    # Research and Publications
                    format_list(data.get('research_papers', [])),
                    format_list(data.get('publications', [])),
                    format_list(data.get('patents', [])),
                    format_list(data.get('research_areas', [])),
                    
                    # Projects
                    format_list(data.get('projects', [])),
                    format_list(data.get('project_technologies', [])),
                    format_list(data.get('project_links', [])),
                    
                    # Leadership and Activities
                    format_list(data.get('leadership_roles', [])),
                    format_list(data.get('volunteer_work', [])),
                    format_list(data.get('extracurricular', [])),
                    
                    # Personal
                    format_list(data.get('interests', [])),
                    format_list(data.get('achievements', [])),
                    
                    # Metadata
                    data.get('original_filename', ''),
                    data.get('created_at', ''),
                    data.get('updated_at', '')
                ])
                
            except Exception as e:
                logger.error(f"Error processing resume in CSV export: {str(e)}")
                # Write basic info if processing fails
                writer.writerow([
                    resume.data.get('candidate_name', 'Unknown'), 
                    resume.data.get('email', ''), 
                    resume.data.get('phone', '')
                ] + [""] * 40)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return "Error generating CSV export"