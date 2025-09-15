# resume_parser.py - Resume Parsing Engine with Error Handling
import re
from collections import Counter
import os

# Try importing required libraries with error handling
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    print("Warning: PyPDF2 not installed. PDF parsing will be disabled.")
    PDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    print("Warning: python-docx not installed. DOCX parsing will be disabled.")
    DOCX_AVAILABLE = False

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
    
    # Download required NLTK data (run once)
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt')

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        print("Downloading NLTK stopwords...")
        nltk.download('stopwords')
        
except ImportError:
    print("Warning: NLTK not installed. Advanced text processing will be limited.")
    NLTK_AVAILABLE = False

class ResumeParser:
    def __init__(self):
        if NLTK_AVAILABLE:
            self.stop_words = set(stopwords.words('english'))
            self.stemmer = PorterStemmer()
        else:
            # Basic stop words if NLTK is not available
            self.stop_words = {
                'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one',
                'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old',
                'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'will', 'have', 'been', 'that',
                'this', 'with', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time',
                'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such',
                'take', 'than', 'them', 'well', 'were'
            }
            self.stemmer = None
        
        # Common skills database (can be expanded)
        self.skills_database = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'go', 'rust', 'kotlin'],
            'web_development': ['html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask'],
            'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sqlite'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins'],
            'data_science': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'tableau', 'powerbi'],
            'project_management': ['agile', 'scrum', 'kanban', 'jira', 'confluence', 'trello'],
            'design': ['photoshop', 'illustrator', 'figma', 'sketch', 'adobe', 'ui/ux', 'graphic design']
        }
        
        # Flatten skills for easy searching
        self.all_skills = []
        for category, skills in self.skills_database.items():
            self.all_skills.extend(skills)
    
    def extract_text_from_file(self, filepath):
        """Extract text from various file formats"""
        text = ""
        file_extension = filepath.lower().split('.')[-1]
        
        try:
            if file_extension == 'pdf':
                if PDF_AVAILABLE:
                    text = self._extract_from_pdf(filepath)
                else:
                    raise Exception("PDF parsing not available. Please install PyPDF2: pip install PyPDF2")
            elif file_extension in ['doc', 'docx']:
                if DOCX_AVAILABLE:
                    text = self._extract_from_docx(filepath)
                else:
                    raise Exception("DOCX parsing not available. Please install python-docx: pip install python-docx")
            elif file_extension == 'txt':
                text = self._extract_from_txt(filepath)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")
        
        return text
    
    def _extract_from_pdf(self, filepath):
        """Extract text from PDF"""
        text = ""
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"PDF extraction error: {str(e)}")
        return text
    
    def _extract_from_docx(self, filepath):
        """Extract text from DOCX"""
        try:
            doc = docx.Document(filepath)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise Exception(f"DOCX extraction error: {str(e)}")
        return text
    
    def _extract_from_txt(self, filepath):
        """Extract text from TXT"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            try:
                # Try with different encoding
                with open(filepath, 'r', encoding='latin-1') as file:
                    text = file.read()
            except Exception as e2:
                raise Exception(f"TXT extraction error: {str(e)} and {str(e2)}")
        return text
    
    def parse_resume(self, filepath):
        """Main function to parse resume and extract structured data"""
        # Extract raw text
        raw_text = self.extract_text_from_file(filepath)
        
        # Parse different sections
        parsed_data = {
            'raw_text': raw_text,
            'contact_info': self._extract_contact_info(raw_text),
            'skills': self._extract_skills(raw_text),
            'experience': self._extract_experience(raw_text),
            'education': self._extract_education(raw_text),
            'keywords': self._extract_keywords(raw_text),
            'summary_stats': self._generate_summary_stats(raw_text)
        }
        
        return parsed_data
    
    def _extract_contact_info(self, text):
        """Extract contact information"""
        contact_info = {}
        
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['email'] = emails[0] if emails else None
        
        # Phone number extraction
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        contact_info['phone'] = ''.join(phones[0]) if phones else None
        
        # LinkedIn extraction
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.findall(linkedin_pattern, text.lower())
        contact_info['linkedin'] = linkedin[0] if linkedin else None
        
        # Name extraction (simple approach - first line or before email)
        lines = text.strip().split('\n')
        potential_name = lines[0].strip() if lines else ""
        # Remove common resume headers
        if not any(word in potential_name.lower() for word in ['resume', 'cv', 'curriculum']):
            contact_info['name'] = potential_name[:50]  # Limit length
        
        return contact_info
    
    def _extract_skills(self, text):
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        # Find skills from our database
        for skill in self.all_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Remove duplicates and sort
        found_skills = list(set(found_skills))
        
        # Categorize skills
        categorized_skills = {}
        for category, skills in self.skills_database.items():
            category_skills = [skill for skill in found_skills if skill.lower() in [s.lower() for s in skills]]
            if category_skills:
                categorized_skills[category] = category_skills
        
        return {
            'all_skills': found_skills,
            'categorized': categorized_skills,
            'skill_count': len(found_skills)
        }
    
    def _extract_experience(self, text):
        """Extract work experience information"""
        # Look for year patterns (e.g., 2020-2023, 2020-present)
        year_pattern = r'(19|20)\d{2}'
        years = re.findall(year_pattern, text)
        
        # Estimate years of experience
        if years:
            years_int = [int(year) for year in years]
            experience_years = max(years_int) - min(years_int) if len(years_int) > 1 else 0
        else:
            experience_years = 0
        
        # Look for job titles (common patterns)
        title_keywords = ['manager', 'developer', 'engineer', 'analyst', 'director', 'specialist', 
                         'coordinator', 'consultant', 'lead', 'senior', 'junior', 'intern']
        
        found_titles = []
        for keyword in title_keywords:
            pattern = r'\b\w*' + keyword + r'\w*\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_titles.extend(matches)
        
        return {
            'estimated_years': experience_years,
            'years_mentioned': years,
            'potential_titles': list(set(found_titles)),
            'title_count': len(set(found_titles))
        }
    
    def _extract_education(self, text):
        """Extract education information"""
        # Degree patterns
        degree_patterns = [
            r'\b(bachelor|master|phd|doctorate|associate|diploma|certificate)\b',
            r'\b(b\.?a\.?|b\.?s\.?|m\.?a\.?|m\.?s\.?|ph\.?d\.?|m\.?b\.?a\.?)\b',
            r'\b(undergraduate|graduate|postgraduate)\b'
        ]
        
        found_degrees = []
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_degrees.extend(matches)
        
        # University/College patterns
        education_institutions = re.findall(r'university|college|institute|school', text, re.IGNORECASE)
        
        return {
            'degrees': list(set(found_degrees)),
            'education_mentioned': len(education_institutions) > 0,
            'degree_count': len(set(found_degrees))
        }
    
    def _extract_keywords(self, text):
        """Extract important keywords using basic or advanced NLP"""
        if NLTK_AVAILABLE:
            return self._extract_keywords_nltk(text)
        else:
            return self._extract_keywords_basic(text)
    
    def _extract_keywords_nltk(self, text):
        """Extract keywords using NLTK"""
        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        if self.stemmer:
            tokens = [self.stemmer.stem(token) for token in tokens]
        
        # Get most common words
        word_freq = Counter(tokens)
        top_keywords = word_freq.most_common(20)
        
        return {
            'top_keywords': top_keywords,
            'total_words': len(tokens),
            'unique_words': len(set(tokens))
        }
    
    def _extract_keywords_basic(self, text):
        """Extract keywords using basic text processing"""
        # Simple word extraction and filtering
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out stop words
        important_words = [word for word in words if word not in self.stop_words and len(word) > 3]
        
        # Get most common words
        word_freq = Counter(important_words)
        top_keywords = word_freq.most_common(20)
        
        return {
            'top_keywords': top_keywords,
            'total_words': len(important_words),
            'unique_words': len(set(important_words))
        }
    
    def _generate_summary_stats(self, text):
        """Generate summary statistics"""
        lines = text.split('\n')
        words = text.split()
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'line_count': len(lines),
            'avg_words_per_line': len(words) / len(lines) if lines else 0
        }