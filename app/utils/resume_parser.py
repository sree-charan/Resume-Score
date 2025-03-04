import os
import re
import logging
import PyPDF2
import nltk
import spacy
from docx import Document
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.chunk import ne_chunk

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('words', quiet=True)

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    import subprocess
    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load('en_core_web_sm')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    """
    Parse resume files (PDF, DOCX, TXT) and extract relevant information
    using improved NLP techniques including spaCy for better entity recognition.
    """
    
    def __init__(self, file_path):
        """Initialize with the path to the resume file"""
        self.file_path = file_path
        self.text = ""
        self.extension = os.path.splitext(file_path)[1].lower()
        self.doc = None  # Will store spaCy doc
        
    def parse(self):
        """
        Main method to parse the resume and extract information.
        Returns a dictionary with parsed data.
        """
        try:
            # Extract text from file
            self.extract_text()
            
            # Process with spaCy
            self.doc = nlp(self.text)
            
            # Parse sections
            sections = self._split_into_sections()
            
            # Parse the text to extract information
            parsed_data = {
                'name': self.extract_name(),
                'email': self.extract_email(),
                'phone': self.extract_phone(),
                'skills': self.extract_skills(),
                'education': self.extract_education(sections.get('education', '')),
                'experience': self.extract_experience(sections.get('experience', '')),
                'sections': sections  # Store all identified sections
            }
            
            logger.info(f"Successfully parsed resume: {self.file_path}")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume {self.file_path}: {str(e)}")
            return {
                'name': '',
                'email': '',
                'phone': '',
                'skills': [],
                'education': '',
                'experience': '',
                'sections': {}
            }

    def _split_into_sections(self):
        """Split resume into sections based on headers"""
        sections = {}
        
        # Common section headers
        section_patterns = {
            'education': r'(?i)(education|academic|qualifications|academic background)',
            'experience': r'(?i)(experience|work|employment|job history|professional background)',
            'skills': r'(?i)(skills|technical skills|core competencies|expertise)',
            'projects': r'(?i)(projects|personal projects|academic projects)',
            'certifications': r'(?i)(certifications|certificates|accreditations)',
            'awards': r'(?i)(awards|achievements|honors)',
            'publications': r'(?i)(publications|research|papers)',
        }
        
        lines = self.text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line is a section header
            found_section = None
            for section, pattern in section_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    found_section = section
                    break
            
            if found_section:
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(section_content)
                # Start new section
                current_section = found_section
                section_content = []
            elif current_section:
                section_content.append(line)
        
        # Save last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)
            
        return sections

    def extract_name(self):
        """Extract candidate's name using spaCy NER"""
        try:
            # Look for PERSON entities in the first few sentences
            first_para = ' '.join(self.text.split('\n')[:5])
            doc = nlp(first_para)
            
            # Filter PERSON entities and validate
            person_names = []
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    name = ent.text.strip()
                    # Basic validation
                    if (len(name.split()) >= 2 and  # At least first and last name
                        not any(char.isdigit() for char in name) and  # No numbers
                        '@' not in name and  # Not an email
                        len(name) < 50):  # Not too long
                        person_names.append(name)
            
            if person_names:
                return person_names[0]
                
            # Fallback to first non-empty line if no valid name found
            first_lines = [line.strip() for line in self.text.split('\n') if line.strip()]
            if first_lines:
                potential_name = first_lines[0]
                if (len(potential_name.split()) <= 5 and
                    not any(char.isdigit() for char in potential_name) and
                    '@' not in potential_name):
                    return potential_name
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting name: {str(e)}")
            return ""

    def extract_email(self):
        """Extract email addresses using improved regex pattern"""
        try:
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, self.text)
            
            # Validate and clean emails
            valid_emails = []
            for email in emails:
                # Basic validation
                if (email.count('@') == 1 and
                    len(email) > 5 and
                    '.' in email.split('@')[1] and
                    not any(c.isspace() for c in email)):
                    valid_emails.append(email.lower())
            
            return valid_emails[0] if valid_emails else ""
            
        except Exception as e:
            logger.error(f"Error extracting email: {str(e)}")
            return ""

    def extract_phone(self):
        """Extract phone numbers using improved regex patterns"""
        try:
            # Multiple phone number patterns
            phone_patterns = [
                r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # International
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US/Canada
                r'\d{10}',  # Simple 10-digit
                r'\+\d{10,}',  # International without formatting
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'  # Simple with separators
            ]
            
            found_numbers = set()
            for pattern in phone_patterns:
                matches = re.finditer(pattern, self.text)
                for match in matches:
                    number = match.group()
                    # Clean the number
                    cleaned = re.sub(r'[^\d+]', '', number)
                    if len(cleaned) >= 10:  # Must have at least 10 digits
                        found_numbers.add(cleaned)
            
            # Format the first found number nicely
            if found_numbers:
                number = list(found_numbers)[0]
                # Format as (XXX) XXX-XXXX for 10-digit numbers
                if len(number) == 10:
                    return f"({number[:3]}) {number[3:6]}-{number[6:]}"
                return number
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting phone: {str(e)}")
            return ""

    def extract_skills(self):
        """Extract skills from the resume"""
        try:
            # Common technical skills and keywords
            common_skills = [
                'python', 'java', 'javascript', 'c\\+\\+', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'typescript',
                'scala', 'rust', 'go', 'perl', 'r', 'matlab', 'objective-c', 'dart', 'shell', 'powershell',
                'html', 'css', 'jquery', 'bootstrap', 'sass', 'less', 'angular', 'react', 'vue', 'node',
                'django', 'flask', 'spring', 'asp\\.net', 'laravel', 'symfony', 'wordpress', 'shopify',
                'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'cassandra', 'redis', 'sqlite',
                'dynamodb', 'firestore', 'couchdb', 'mariadb', 'mssql', 'neo4j',
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digital ocean', 'firebase',
                'cloudflare', 'vercel', 'netlify',
                'docker', 'kubernetes', 'jenkins', 'gitlab', 'github actions', 'terraform', 'ansible',
                'chef', 'puppet', 'circleci', 'travis', 'prometheus', 'grafana',
                'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
                'pandas', 'numpy', 'scipy', 'data analysis', 'data visualization', 'jupyter',
                'tableau', 'power bi', 'hadoop', 'spark', 'kafka',
                'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic', 'cordova',
                'mobile development',
                'git', 'agile', 'scrum', 'jira', 'rest api', 'graphql', 'microservices',
                'unit testing', 'ci/cd', 'serverless', 'blockchain', 'ai', 'nlp',
                'leadership', 'communication', 'teamwork', 'problem solving', 'time management',
                'project management', 'critical thinking', 'creativity', 'collaboration'
            ]
            
            # Create a regex pattern to find skills
            skill_pattern = r'\b(' + '|'.join(common_skills) + r')\b'
            found_skills = set()
            
            # Find all matches, case insensitive
            matches = re.finditer(skill_pattern, self.text.lower())
            for match in matches:
                skill = match.group(0)
                found_skills.add(skill)
                
            return list(found_skills)
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []
    
    def extract_education(self, education_text=None):
        """
        Extract education information with improved detection of degrees,
        universities, and graduation years
        """
        try:
            text_to_analyze = education_text or self.text
            
            # Common degree keywords
            degrees = [
                'phd', 'ph.d', 'doctorate',
                'master', 'ms', 'msc', 'm.s', 'm.sc', 'ma', 'm.a', 'mba', 'm.b.a',
                'bachelor', 'bs', 'bsc', 'b.s', 'b.sc', 'ba', 'b.a',
                'associate', 'as', 'a.s',
            ]
            
            education_info = []
            
            # Process with spaCy for organization detection
            doc = nlp(text_to_analyze)
            
            # Find organizations (potential universities) and dates
            universities = set()
            dates = set()
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    universities.add(ent.text)
                elif ent.label_ == 'DATE':
                    dates.add(ent.text)
            
            # Find degrees
            found_degrees = []
            for line in text_to_analyze.split('\n'):
                line_lower = line.lower()
                for degree in degrees:
                    if f' {degree} ' in f' {line_lower} ':
                        found_degrees.append(line.strip())
                        break
            
            # Combine information
            if found_degrees:
                education_info.extend(found_degrees)
            if universities:
                education_info.extend(universities)
            if dates:
                education_info.extend(f"({date})" for date in dates)
            
            return "\n".join(education_info) if education_info else ""
            
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}")
            return ""

    def extract_experience(self, experience_text=None):
        """Extract work experience information from the resume"""
        try:
            text_to_analyze = experience_text or self.text
            
            # Look for sections that might contain experience info
            experience_keywords = [
                'experience', 'work history', 'employment', 'job history', 
                'professional experience', 'work experience', 'career'
            ]
            experience_pattern = r'(?i)(' + '|'.join(experience_keywords) + r').*?(?:\n\n|\Z)'
            
            exp_sections = re.findall(experience_pattern, text_to_analyze, re.DOTALL)
            if exp_sections:
                return exp_sections[0][:500]  # Return first 500 chars
                
            # Alternative approach: extract sentences containing experience keywords
            sentences = sent_tokenize(text_to_analyze)
            experience_info = []
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in experience_keywords):
                    experience_info.append(sentence)
                    
            return ' '.join(experience_info[:5]) if experience_info else ""
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}")
            return ""