# resume_parser.py - Resume Parsing Engine
import PyPDF2
import docx
import re
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import os

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ResumeParser:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.stemmer = PorterStemmer()
        
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
        
        # Enhanced phone number patterns
        self.phone_patterns = [
            # US formats
            r'\+?1[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            # International formats
            r'\+[0-9]{1,4}[-.\s]?\(?[0-9]{1,4}\)?[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
            # General patterns
            r'[0-9]{3}[-.\s][0-9]{3}[-.\s][0-9]{4}',
            r'\([0-9]{3}\)\s*[0-9]{3}[-.\s]?[0-9]{4}',
            # 10-digit numbers
            r'\b[0-9]{10}\b'
        ]
    
    def extract_text_from_file(self, filepath):
        """Extract text from various file formats"""
        text = ""
        file_extension = filepath.lower().split('.')[-1]
        
        try:
            if file_extension == 'pdf':
                text = self._extract_from_pdf(filepath)
            elif file_extension in ['doc', 'docx']:
                text = self._extract_from_docx(filepath)
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
            raise Exception(f"TXT extraction error: {str(e)}")
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
        """Enhanced contact information extraction"""
        contact_info = {}
        
        # Enhanced email extraction
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b'
        ]
        
        emails = []
        for pattern in email_patterns:
            emails.extend(re.findall(pattern, text))
        
        # Clean and validate emails
        valid_emails = []
        for email in emails:
            email = email.strip().replace(' ', '')
            if '@' in email and '.' in email.split('@')[1]:
                valid_emails.append(email)
        
        contact_info['email'] = valid_emails[0] if valid_emails else None
        
        # Enhanced phone number extraction
        phones = []
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    # Reconstruct phone from groups
                    phone = ''.join(match)
                else:
                    phone = match
                
                # Clean phone number
                phone = re.sub(r'[^\d]', '', phone)
                
                # Validate phone length (US: 10 digits, International: 7-15 digits)
                if 7 <= len(phone) <= 15:
                    phones.append(phone)
        
        # Format the best phone number
        if phones:
            best_phone = phones[0]
            if len(best_phone) == 10:
                # Format US number: (XXX) XXX-XXXX
                formatted = f"({best_phone[:3]}) {best_phone[3:6]}-{best_phone[6:]}"
            else:
                formatted = best_phone
            contact_info['phone'] = formatted
        else:
            contact_info['phone'] = None
        
        # Enhanced LinkedIn extraction
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'linkedin\.com/pub/[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+',
            r'https?://(?:www\.)?linkedin\.com/in/[\w-]+'
        ]
        
        linkedin_urls = []
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, text.lower())
            linkedin_urls.extend(matches)
        
        if linkedin_urls:
            # Clean up the URL
            linkedin = linkedin_urls[0]
            if not linkedin.startswith('http'):
                linkedin = 'https://' + linkedin
            contact_info['linkedin'] = linkedin
        else:
            contact_info['linkedin'] = None
        
        # Enhanced name extraction
        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
        
        # Look for name in first few lines
        potential_names = []
        for i, line in enumerate(lines[:5]):
            # Skip lines with common resume headers
            skip_keywords = ['resume', 'cv', 'curriculum', 'vitae', '@', 'phone', 'email', 'address']
            if not any(keyword in line.lower() for keyword in skip_keywords):
                # Check if line looks like a name (2-4 words, mostly letters)
                words = line.split()
                if 2 <= len(words) <= 4:
                    if all(word.isalpha() or word.replace('.', '').isalpha() for word in words):
                        potential_names.append(line)
        
        contact_info['name'] = potential_names[0][:50] if potential_names else None
        
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
        """Extract important keywords using NLP"""
        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        tokens = [self.stemmer.stem(token) for token in tokens]
        
        # Get most common words
        word_freq = Counter(tokens)
        top_keywords = word_freq.most_common(20)
        
        return {
            'top_keywords': top_keywords,
            'total_words': len(tokens),
            'unique_words': len(set(tokens))
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