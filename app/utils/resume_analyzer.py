import re
import nltk
import spacy
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

# Download necessary NLTK data
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Load spaCy and BERT models
try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    import subprocess
    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load('en_core_web_sm')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeAnalyzer:
    """
    Analyze resumes against job descriptions using advanced NLP techniques
    including semantic similarity and detailed scoring.
    """
    
    def __init__(self, resume_data, job_description_text):
        """
        Initialize the analyzer with parsed resume data and job description text
        """
        self.resume_data = resume_data
        self.job_description = job_description_text
        self.job_skills = self._extract_skills_from_text(job_description_text)
        self.required_skills = self._identify_required_skills()
        
        # Load BERT model for semantic similarity
        try:
            self.bert_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        except Exception as e:
            logger.error(f"Error loading BERT model: {str(e)}")
            self.bert_model = None
        
        # Initialize NLP tools
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
    def calculate_score(self, weights=None):
        """
        Calculate an overall relevance score with detailed breakdown
        
        Args:
            weights (dict): Custom weights for different score components
        
        Returns:
            dict: Detailed scoring information including:
                - overall_score: float between 0 and 100
                - component_scores: dict of individual component scores
                - matched_skills: list of matched skills
                - missing_skills: list of missing required skills
                - skill_contexts: dict mapping skills to where they were found
                - experience_matches: list of relevant experience matches
                - education_matches: list of education matches
        """
        if weights is None:
            weights = {
                'skills_match': 0.35,
                'required_skills': 0.25,
                'experience_match': 0.20,
                'education_match': 0.10,
                'overall_similarity': 0.10
            }
            
        try:
            # Calculate individual scores with detailed information
            skills_analysis = self._analyze_skills_match()
            experience_analysis = self._analyze_experience_match()
            education_analysis = self._analyze_education_match()
            similarity_analysis = self._calculate_semantic_similarity()
            
            # Calculate weighted score
            weighted_score = (
                (skills_analysis['score'] * weights['skills_match']) +
                (skills_analysis['required_score'] * weights['required_skills']) +
                (experience_analysis['score'] * weights['experience_match']) +
                (education_analysis['score'] * weights['education_match']) +
                (similarity_analysis['score'] * weights['overall_similarity'])
            ) * 100
            
            # Prepare detailed results
            detailed_results = {
                'overall_score': round(weighted_score, 2),
                'component_scores': {
                    'skills_match': round(skills_analysis['score'] * 100, 2),
                    'required_skills_match': round(skills_analysis['required_score'] * 100, 2),
                    'experience_match': round(experience_analysis['score'] * 100, 2),
                    'education_match': round(education_analysis['score'] * 100, 2),
                    'semantic_similarity': round(similarity_analysis['score'] * 100, 2)
                },
                'skills_analysis': {
                    'matched_skills': skills_analysis['matched_skills'],
                    'missing_skills': skills_analysis['missing_skills'],
                    'skill_contexts': skills_analysis['skill_contexts'],
                    'required_skills': self.required_skills
                },
                'experience_analysis': experience_analysis['details'],
                'education_analysis': education_analysis['details'],
                'similarity_analysis': similarity_analysis['details']
            }
            
            logger.info(f"Resume analysis complete. Overall score: {weighted_score:.2f}%")
            return detailed_results
            
        except Exception as e:
            logger.error(f"Error calculating resume score: {str(e)}")
            return {
                'overall_score': 0.0,
                'component_scores': {},
                'skills_analysis': {},
                'experience_analysis': {},
                'education_analysis': {},
                'similarity_analysis': {}
            }
    
    def _identify_required_skills(self):
        """
        Identify required skills from job description using keyword analysis
        """
        required_skills = set()
        text_lower = self.job_description.lower()
        
        # Look for requirement indicators
        requirement_patterns = [
            r'required skills?:?(.*?)(?:\n\n|\Z)',
            r'requirements?:?(.*?)(?:\n\n|\Z)',
            r'must have:?(.*?)(?:\n\n|\Z)',
            r'essential skills?:?(.*?)(?:\n\n|\Z)',
            r'key skills?:?(.*?)(?:\n\n|\Z)'
        ]
        
        # Look for requirement keywords
        requirement_keywords = ['required', 'must have', 'essential', 'necessary']
        
        # Extract skills from requirement sections
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, text_lower, re.DOTALL)
            for match in matches:
                skills = self._extract_skills_from_text(match.group(1))
                required_skills.update(skills)
        
        # Look for skills with requirement keywords
        lines = text_lower.split('\n')
        for line in lines:
            if any(keyword in line for keyword in requirement_keywords):
                skills = self._extract_skills_from_text(line)
                required_skills.update(skills)
        
        return list(required_skills)
    
    def _analyze_skills_match(self):
        """
        Analyze skills match with detailed context
        """
        resume_skills = set(self.resume_data['skills'])
        job_skills = set(self.job_skills)
        required_skills = set(self.required_skills)
        
        # Find matches and missing skills
        matched_skills = resume_skills.intersection(job_skills)
        missing_skills = job_skills - resume_skills
        missing_required = required_skills - resume_skills
        
        # Find context for matched skills
        skill_contexts = {}
        for skill in matched_skills:
            contexts = self._find_skill_context(skill)
            if contexts:
                skill_contexts[skill] = contexts
        
        # Calculate scores
        skills_score = len(matched_skills) / len(job_skills) if job_skills else 0.0
        required_score = (len(required_skills) - len(missing_required)) / len(required_skills) if required_skills else 1.0
        
        return {
            'score': min(skills_score, 1.0),
            'required_score': min(required_score, 1.0),
            'matched_skills': list(matched_skills),
            'missing_skills': list(missing_skills),
            'skill_contexts': skill_contexts
        }
    
    def _find_skill_context(self, skill):
        """Find where a skill is mentioned in the resume"""
        contexts = []
        
        # Look in experience section
        if self.resume_data.get('experience'):
            sentences = nltk.sent_tokenize(self.resume_data['experience'])
            for sentence in sentences:
                if skill.lower() in sentence.lower():
                    contexts.append(('experience', sentence.strip()))
        
        # Look in education section
        if self.resume_data.get('education'):
            sentences = nltk.sent_tokenize(self.resume_data['education'])
            for sentence in sentences:
                if skill.lower() in sentence.lower():
                    contexts.append(('education', sentence.strip()))
        
        # Look in other sections
        if self.resume_data.get('sections'):
            for section, content in self.resume_data['sections'].items():
                if section not in ['experience', 'education']:
                    sentences = nltk.sent_tokenize(content)
                    for sentence in sentences:
                        if skill.lower() in sentence.lower():
                            contexts.append((section, sentence.strip()))
        
        return contexts
    
    def _analyze_experience_match(self):
        """
        Analyze experience match using semantic similarity and pattern matching
        """
        resume_experience = self.resume_data.get('experience', '')
        if not resume_experience or not self.job_description:
            return {'score': 0.0, 'details': []}
        
        details = []
        total_score = 0.0
        
        # Extract experience requirements from job description
        experience_patterns = [
            r'(\d+)[+\s]*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
            r'experience:\s*(\d+)[+\s]*(?:years?|yrs?)',
            r'(?:minimum|min)\s+(\d+)\s+(?:years?|yrs?)'
        ]
        
        required_years = 0
        for pattern in experience_patterns:
            matches = re.finditer(pattern, self.job_description.lower())
            for match in matches:
                years = int(match.group(1))
                if years > required_years:
                    required_years = years
        
        # Extract years from resume experience
        resume_years = 0
        year_patterns = [
            r'(\d+)[+\s]*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
            r'(?:19|20)\d{2}\s*-\s*(?:present|current|now|(?:19|20)\d{2})',
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(?:19|20)\d{2}'
        ]
        
        for pattern in year_patterns:
            matches = re.finditer(pattern, resume_experience.lower())
            for match in matches:
                if '-' in match.group():
                    # Handle date ranges
                    start, end = match.group().split('-')
                    if 'present' in end.lower() or 'current' in end.lower() or 'now' in end.lower():
                        from datetime import datetime
                        end_year = datetime.now().year
                    else:
                        end_year = int(re.search(r'(?:19|20)\d{2}', end).group())
                    start_year = int(re.search(r'(?:19|20)\d{2}', start).group())
                    resume_years += end_year - start_year
                else:
                    # Direct year mention
                    years = int(re.search(r'\d+', match.group()).group())
                    if years > resume_years:
                        resume_years = years
        
        # Score based on years of experience
        if required_years > 0:
            years_score = min(resume_years / required_years, 1.0)
            details.append({
                'type': 'years',
                'required': required_years,
                'found': resume_years,
                'score': years_score
            })
            total_score += years_score * 0.5  # Weight: 50%
        
        # Calculate semantic similarity of experience descriptions
        if self.bert_model:
            try:
                # Split into chunks to handle long text
                resume_chunks = [s.strip() for s in resume_experience.split('\n') if s.strip()]
                job_chunks = [s.strip() for s in self.job_description.split('\n') if s.strip()]
                
                # Get embeddings
                resume_embeddings = self.bert_model.encode(resume_chunks)
                job_embeddings = self.bert_model.encode(job_chunks)
                
                # Calculate similarity
                similarities = cosine_similarity(resume_embeddings, job_embeddings)
                max_similarities = np.max(similarities, axis=1)
                semantic_score = np.mean(max_similarities)
                
                details.append({
                    'type': 'semantic',
                    'score': semantic_score,
                    'matches': [
                        {
                            'resume_text': resume_chunks[i],
                            'job_text': job_chunks[np.argmax(similarities[i])],
                            'similarity': max_similarities[i]
                        }
                        for i in range(len(resume_chunks))
                        if max_similarities[i] > 0.7  # Only include strong matches
                    ]
                })
                total_score += semantic_score * 0.5  # Weight: 50%
            except Exception as e:
                logger.error(f"Error in semantic analysis: {str(e)}")
        
        return {
            'score': total_score,
            'details': details
        }
    
    def _analyze_education_match(self):
        """
        Analyze education match with detailed comparison
        """
        resume_education = self.resume_data.get('education', '')
        if not resume_education:
            return {'score': 0.0, 'details': []}
        
        details = []
        total_score = 0.0
        
        # Education level hierarchy
        education_levels = {
            'phd': 5,
            'doctorate': 5,
            'masters': 4,
            'bachelors': 3,
            'associate': 2,
            'high school': 1
        }
        
        # Find required education level in job description
        required_level = None
        required_level_score = 0
        for level, score in education_levels.items():
            if level in self.job_description.lower():
                if score > required_level_score:
                    required_level = level
                    required_level_score = score
        
        # Find candidate's education level
        candidate_level = None
        candidate_level_score = 0
        for level, score in education_levels.items():
            if level in resume_education.lower():
                if score > candidate_level_score:
                    candidate_level = level
                    candidate_level_score = score
        
        # Score based on education level match
        if required_level:
            if candidate_level_score >= required_level_score:
                level_score = 1.0
            else:
                level_score = candidate_level_score / required_level_score
            
            details.append({
                'type': 'level',
                'required': required_level,
                'found': candidate_level,
                'score': level_score
            })
            total_score += level_score * 0.6  # Weight: 60%
        
        # Look for field of study match
        fields_of_study = [
            'computer science', 'software engineering', 'information technology',
            'engineering', 'mathematics', 'physics', 'business', 'data science',
            'artificial intelligence', 'machine learning', 'cybersecurity'
        ]
        
        required_fields = []
        candidate_fields = []
        
        for field in fields_of_study:
            if field in self.job_description.lower():
                required_fields.append(field)
            if field in resume_education.lower():
                candidate_fields.append(field)
        
        if required_fields:
            field_matches = set(required_fields).intersection(set(candidate_fields))
            field_score = len(field_matches) / len(required_fields)
            
            details.append({
                'type': 'field',
                'required': required_fields,
                'found': candidate_fields,
                'matches': list(field_matches),
                'score': field_score
            })
            total_score += field_score * 0.4  # Weight: 40%
        elif candidate_fields:
            # If no specific field required, give partial credit for relevant fields
            details.append({
                'type': 'field',
                'found': candidate_fields,
                'score': 0.5
            })
            total_score += 0.5 * 0.4  # Weight: 40%
        
        return {
            'score': total_score,
            'details': details
        }
    
    def _calculate_semantic_similarity(self):
        """
        Calculate overall semantic similarity between resume and job description
        """
        if not self.bert_model:
            return {'score': 0.0, 'details': {}}
        
        try:
            # Combine all resume text
            resume_text = ' '.join([
                self.resume_data.get('name', ''),
                self.resume_data.get('email', ''),
                self.resume_data.get('phone', ''),
                ' '.join(self.resume_data.get('skills', [])),
                self.resume_data.get('education', ''),
                self.resume_data.get('experience', '')
            ])
            
            # Get embeddings
            resume_embedding = self.bert_model.encode([resume_text])
            job_embedding = self.bert_model.encode([self.job_description])
            
            # Calculate similarity
            similarity = cosine_similarity(resume_embedding, job_embedding)[0][0]
            
            return {
                'score': min(similarity, 1.0),
                'details': {
                    'similarity_score': similarity,
                    'method': 'BERT semantic similarity'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in semantic similarity calculation: {str(e)}")
            return {'score': 0.0, 'details': {'error': str(e)}}
    
    def _extract_skills_from_text(self, text):
        """
        Extract skills from text using a keyword-based approach.
        
        Args:
            text (str): Text to extract skills from
            
        Returns:
            list: List of skills found in the text
        """
        # Same list of common skills used in ResumeParser
        common_skills = [
            # Programming languages
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'typescript',
            'scala', 'rust', 'go', 'perl', 'r', 'matlab', 'objective-c', 'dart', 'shell', 'powershell',
            
            # Web development
            'html', 'css', 'jquery', 'bootstrap', 'sass', 'less', 'angular', 'react', 'vue', 'node',
            'django', 'flask', 'spring', 'asp.net', 'laravel', 'symfony', 'wordpress', 'shopify',
            
            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'cassandra', 'redis', 'sqlite',
            'dynamodb', 'firestore', 'couchdb', 'mariadb', 'mssql', 'neo4j',
            
            # Cloud platforms
            'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digital ocean', 'firebase',
            'cloudflare', 'vercel', 'netlify',
            
            # DevOps
            'docker', 'kubernetes', 'jenkins', 'gitlab', 'github actions', 'terraform', 'ansible',
            'chef', 'puppet', 'circleci', 'travis', 'prometheus', 'grafana',
            
            # Data science
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
            'pandas', 'numpy', 'scipy', 'data analysis', 'data visualization', 'jupyter',
            'tableau', 'power bi', 'hadoop', 'spark', 'kafka',
            
            # Mobile
            'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic', 'cordova',
            'mobile development',
            
            # Other technical skills
            'git', 'agile', 'scrum', 'jira', 'rest api', 'graphql', 'microservices',
            'unit testing', 'ci/cd', 'serverless', 'blockchain', 'ai', 'nlp',
            
            # Soft skills
            'leadership', 'communication', 'teamwork', 'problem solving', 'time management',
            'project management', 'critical thinking', 'creativity', 'collaboration'
        ]
        
        found_skills = set()
        
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Look for skill keywords in the text
        for skill in common_skills:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
                
        return list(found_skills)
    
    def _preprocess_text(self, text):
        """
        Preprocess text for NLP analysis:
        - Tokenize
        - Remove stopwords
        - Lemmatize
        
        Args:
            text (str): Text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and non-alphabetic tokens
        filtered_tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        
        # Lemmatize
        lemmatized_tokens = [self.lemmatizer.lemmatize(token) for token in filtered_tokens]
        
        return ' '.join(lemmatized_tokens)