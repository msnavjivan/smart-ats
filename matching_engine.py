# matching_engine.py - Enhanced Candidate Matching and Suggestion Engine
import re
from collections import Counter
import math

class MatchingEngine:
    def __init__(self):
        # Enhanced weights for better matching
        self.weights = {
            'skills_match': 0.35,
            'experience_match': 0.20,
            'education_match': 0.15,
            'keyword_match': 0.20,
            'dynamic_keyword_match': 0.10  # New: Dynamic keywords from job description
        }
        
        # Enhanced education level hierarchy
        self.education_hierarchy = {
            'high school': 1,
            'diploma': 2,
            'certificate': 2,
            'associate': 3,
            'bachelor': 4,
            'master': 5,
            'mba': 6,
            'phd': 7,
            'doctorate': 7
        }
    
    def extract_job_keywords(self, job_description):
        """Extract dynamic keywords from job description using NLP techniques"""
        if not job_description:
            return []
        
        # Clean and tokenize
        text = job_description.lower()
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her',
            'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its',
            'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use',
            'way', 'will', 'have', 'been', 'that', 'this', 'with', 'from', 'they', 'know',
            'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here',
            'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them',
            'well', 'were', 'what', 'your', 'work', 'years', 'would', 'there', 'said',
            'each', 'which', 'their', 'called', 'other', 'made', 'more', 'find', 'where',
            'should', 'must', 'able', 'experience', 'candidate', 'position', 'role', 'job'
        }
        
        # Extract meaningful words (3+ characters, not numbers)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        meaningful_words = [word for word in words if word not in stop_words]
        
        # Count frequency
        word_freq = Counter(meaningful_words)
        
        # Extract technical terms and skills
        technical_patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms (AWS, API, SQL)
            r'\b\w*(?:js|sql|api|sdk|ide|ui|ux|css|html|xml|json)\b',  # Technical suffixes
            r'\b(?:python|java|javascript|react|angular|node|docker|kubernetes|aws|azure|gcp)\b',  # Popular techs
        ]
        
        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technical_terms.extend(matches)
        
        # Score and rank keywords
        scored_keywords = []
        
        # Single word keywords (higher frequency = higher score)
        for word, freq in word_freq.most_common(30):
            score = freq
            
            # Boost technical terms
            if word.lower() in [t.lower() for t in technical_terms]:
                score *= 2
            
            # Boost longer, more specific terms
            if len(word) > 6:
                score *= 1.2
            
            scored_keywords.append({
                'keyword': word,
                'score': score,
                'type': 'single',
                'frequency': freq
            })
        
        return scored_keywords
    
    # Keep the original method for backward compatibility
    def match_candidates(self, job_data, candidates):
        """Original method - kept for compatibility"""
        return self.match_candidates_enhanced(job_data, candidates)
    
    def match_candidates_enhanced(self, job_data, candidates):
        """Enhanced candidate matching with dynamic keywords"""
        matches = []
        
        for candidate in candidates:
            match_score = self._calculate_enhanced_match_score(job_data, candidate['parsed_data'])
            
            matches.append({
                'candidate': candidate,
                'match_score': match_score['total_score'],
                'match_breakdown': match_score['breakdown'],
                'strengths': match_score['strengths'],
                'gaps': match_score['gaps']
            })
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches
    
    def _calculate_enhanced_match_score(self, job_data, candidate_data):
        """Enhanced matching algorithm with better keyword matching"""
        
        # Skills matching (enhanced)
        skills_score = self._calculate_skills_match_enhanced(
            job_data.get('required_skills', []), 
            candidate_data['skills']['all_skills']
        )
        
        # Experience matching
        experience_score = self._calculate_experience_match(
            job_data.get('experience_years', 0),
            candidate_data['experience']['estimated_years']
        )
        
        # Education matching
        education_score = self._calculate_education_match(
            job_data.get('education_level', ''),
            candidate_data['education']['degrees']
        )
        
        # Keyword matching (enhanced)
        keyword_score = self._calculate_keyword_match_enhanced(
            job_data.get('description', ''),
            candidate_data.get('raw_text', '')
        )
        
        # Dynamic keyword matching (NEW)
        dynamic_keyword_score = self._calculate_dynamic_keyword_match(
            job_data.get('dynamic_keywords', []),
            candidate_data.get('raw_text', '')
        )
        
        # Calculate weighted total score
        total_score = (
            skills_score['score'] * self.weights['skills_match'] +
            experience_score['score'] * self.weights['experience_match'] +
            education_score['score'] * self.weights['education_match'] +
            keyword_score['score'] * self.weights['keyword_match'] +
            dynamic_keyword_score['score'] * self.weights['dynamic_keyword_match']
        )
        
        # Enhanced strengths and gaps analysis
        strengths = []
        gaps = []
        
        # Skills analysis
        if skills_score['score'] > 0.8:
            strengths.append(f"Excellent skills match ({skills_score['matched_count']}/{skills_score['total_required']} required skills)")
        elif skills_score['score'] > 0.6:
            strengths.append(f"Good skills match ({skills_score['matched_count']}/{skills_score['total_required']} required skills)")
        elif skills_score['score'] < 0.4:
            gaps.append(f"Missing key skills ({skills_score['missing_count']} out of {skills_score['total_required']} required)")
        
        # Experience analysis
        if experience_score['score'] > 0.9:
            strengths.append("Perfect experience level match")
        elif experience_score['score'] > 0.7:
            strengths.append("Good experience level")
        elif experience_score['score'] < 0.5:
            exp_gap = job_data.get('experience_years', 0) - candidate_data['experience'].get('estimated_years', 0)
            if exp_gap > 0:
                gaps.append(f"May need {exp_gap} more years of experience")
        
        # Education analysis
        if education_score['score'] > 0.8:
            strengths.append("Strong educational background")
        elif education_score['score'] < 0.3 and job_data.get('education_level'):
            gaps.append("Education level may not meet requirements")
        
        # Dynamic keyword analysis
        if dynamic_keyword_score['score'] > 0.7:
            strengths.append(f"Strong keyword alignment ({dynamic_keyword_score['matched_count']} key terms matched)")
        elif dynamic_keyword_score['score'] < 0.3:
            gaps.append("Limited alignment with job-specific requirements")
        
        return {
            'total_score': round(total_score * 100, 2),
            'breakdown': {
                'skills': round(skills_score['score'] * 100, 2),
                'experience': round(experience_score['score'] * 100, 2),
                'education': round(education_score['score'] * 100, 2),
                'keywords': round(keyword_score['score'] * 100, 2),
                'dynamic_keywords': round(dynamic_keyword_score['score'] * 100, 2)
            },
            'strengths': strengths,
            'gaps': gaps
        }
    
    def _calculate_skills_match_enhanced(self, required_skills, candidate_skills):
        """Enhanced skills matching with synonym recognition"""
        if not required_skills:
            return {'score': 1.0, 'matched_count': 0, 'missing_count': 0, 'total_required': 0}
        
        # Get candidate skills
        candidate_skills_lower = [skill.lower().strip() for skill in candidate_skills]
        
        # Enhanced skill synonyms
        skill_synonyms = {
            'javascript': ['js', 'ecmascript', 'node.js', 'nodejs'],
            'python': ['py'],
            'react': ['reactjs', 'react.js'],
            'angular': ['angularjs', 'angular.js'],
            'machine learning': ['ml', 'artificial intelligence', 'ai'],
            'amazon web services': ['aws'],
            'microsoft azure': ['azure'],
            'google cloud': ['gcp', 'google cloud platform'],
            'docker': ['containerization'],
            'kubernetes': ['k8s', 'container orchestration'],
            'sql': ['mysql', 'postgresql', 'database'],
            'css': ['css3', 'cascading style sheets'],
            'html': ['html5', 'hypertext markup language']
        }
        
        matched_skills = []
        missing_skills = []
        
        for required_skill in required_skills:
            if not required_skill.strip():
                continue
                
            required_lower = required_skill.lower().strip()
            matched = False
            
            # Direct match
            if required_lower in candidate_skills_lower:
                matched_skills.append(required_skill)
                matched = True
            else:
                # Check synonyms and partial matches
                for candidate_skill in candidate_skills_lower:
                    # Check if required skill is contained in candidate skill
                    if required_lower in candidate_skill or candidate_skill in required_lower:
                        matched_skills.append(required_skill)
                        matched = True
                        break
                    
                    # Check synonym dictionary
                    for main_skill, synonyms in skill_synonyms.items():
                        if (required_lower == main_skill and candidate_skill in synonyms) or \
                           (required_lower in synonyms and candidate_skill == main_skill):
                            matched_skills.append(required_skill)
                            matched = True
                            break
                    
                    if matched:
                        break
            
            if not matched:
                missing_skills.append(required_skill)
        
        total_required = len([s for s in required_skills if s.strip()])
        match_ratio = len(matched_skills) / total_required if total_required > 0 else 0
        
        return {
            'score': match_ratio,
            'matched_count': len(matched_skills),
            'missing_count': len(missing_skills),
            'total_required': total_required
        }
    
    # Keep original methods for backward compatibility
    def _calculate_skills_match(self, required_skills, candidate_skills):
        """Original skills matching - kept for compatibility"""
        return self._calculate_skills_match_enhanced(required_skills, candidate_skills)
    
    def _calculate_match_score(self, job_data, candidate_data):
        """Original method - kept for compatibility"""
        return self._calculate_enhanced_match_score(job_data, candidate_data)
    
    def _skills_similar(self, skill1, skill2):
        """Check if two skills are similar (simple similarity check)"""
        # Simple fuzzy matching for common variations
        synonyms = {
            'js': 'javascript',
            'react.js': 'react',
            'node.js': 'nodejs',
            'ai': 'artificial intelligence',
            'ml': 'machine learning'
        }
        
        skill1 = synonyms.get(skill1, skill1)
        skill2 = synonyms.get(skill2, skill2)
        
        # Check if one skill contains the other (with length consideration)
        if len(skill1) > 2 and len(skill2) > 2:
            return skill1 in skill2 or skill2 in skill1
        
        return skill1 == skill2
    
    def _calculate_experience_match(self, required_years, candidate_years):
        """Calculate experience matching score"""
        if required_years == 0:
            return {'score': 1.0}
        
        if candidate_years >= required_years:
            # Perfect match or overqualified (slight penalty for being too overqualified)
            if candidate_years <= required_years * 2:
                score = 1.0
            else:
                score = 0.9  # Slight penalty for being very overqualified
        else:
            # Underqualified - score decreases as gap increases
            gap_ratio = candidate_years / required_years
            score = max(0.1, gap_ratio)  # Minimum score of 0.1
        
        return {'score': score}
    
    def _calculate_education_match(self, required_education, candidate_degrees):
        """Calculate education matching score"""
        if not required_education or not required_education.strip():
            return {'score': 1.0}
        
        required_level = self._get_education_level(required_education)
        candidate_level = max([self._get_education_level(degree) for degree in candidate_degrees], default=0)
        
        if candidate_level >= required_level:
            return {'score': 1.0}
        elif candidate_level == 0:
            return {'score': 0.3}  # Some credit for having any education mentioned
        else:
            # Partial credit based on how close they are
            score = candidate_level / required_level
            return {'score': min(1.0, score)}
    
    def _get_education_level(self, education_text):
        """Get numeric education level from text"""
        education_lower = education_text.lower()
        
        for level_name, level_value in self.education_hierarchy.items():
            if level_name in education_lower:
                return level_value
        
        return 0
    
    def _calculate_keyword_match(self, job_description, candidate_text):
        """Original keyword matching - kept for compatibility"""
        return self._calculate_keyword_match_enhanced(job_description, candidate_text)
    
    def _calculate_keyword_match_enhanced(self, job_description, candidate_text):
        """Enhanced keyword matching"""
        if not job_description:
            return {'score': 1.0}
        
        # Extract meaningful keywords from both texts
        job_keywords = self._extract_meaningful_keywords(job_description)
        candidate_keywords = self._extract_meaningful_keywords(candidate_text)
        
        if not job_keywords:
            return {'score': 1.0}
        
        # Calculate overlap with TF-IDF-like scoring
        job_freq = Counter(job_keywords)
        candidate_freq = Counter(candidate_keywords)
        
        total_score = 0
        max_possible_score = 0
        
        for keyword, job_count in job_freq.items():
            candidate_count = candidate_freq.get(keyword, 0)
            
            # Score based on frequency in both documents
            keyword_score = min(job_count, candidate_count) / job_count
            total_score += keyword_score * job_count
            max_possible_score += job_count
        
        final_score = total_score / max_possible_score if max_possible_score > 0 else 0
        return {'score': min(1.0, final_score)}
    
    def _calculate_dynamic_keyword_match(self, dynamic_keywords, candidate_text):
        """Match against dynamically extracted keywords"""
        if not dynamic_keywords:
            return {'score': 1.0, 'matched_count': 0}
        
        candidate_text_lower = candidate_text.lower()
        matches = []
        total_score = 0
        max_possible_score = 0
        
        for keyword_data in dynamic_keywords:
            keyword = keyword_data['keyword'].lower()
            importance_score = keyword_data['score']
            
            # Check if keyword exists in candidate text
            if keyword in candidate_text_lower:
                # Count occurrences
                occurrences = candidate_text_lower.count(keyword)
                match_score = min(1.0, occurrences / keyword_data['frequency']) * importance_score
                
                matches.append(keyword)
                total_score += match_score
            
            max_possible_score += importance_score
        
        final_score = total_score / max_possible_score if max_possible_score > 0 else 0
        
        return {
            'score': min(1.0, final_score),
            'matched_count': len(matches)
        }
    
    def _extract_meaningful_keywords(self, text):
        """Extract meaningful keywords from text"""
        if not text:
            return []
        
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Enhanced stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her',
            'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its',
            'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use',
            'way', 'will', 'have', 'been', 'that', 'this', 'with', 'from', 'they', 'know',
            'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here',
            'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them',
            'well', 'were', 'what', 'your', 'work', 'years', 'would', 'there', 'said',
            'each', 'which', 'their', 'called', 'other', 'made', 'more', 'find', 'where'
        }
        
        # Filter meaningful words
        meaningful_words = []
        for word in words:
            if (word not in stop_words and 
                len(word) > 3 and 
                not word.isdigit() and
                word.isalpha()):
                meaningful_words.append(word)
        
        return meaningful_words
    
    def _extract_important_words(self, text):
        """Extract important words from text (kept for compatibility)"""
        return self._extract_meaningful_keywords(text)
    
    def generate_suggestions(self, candidate_data):
        """Enhanced suggestion generation"""
        suggestions = []
        
        # Skills suggestions
        skills_count = candidate_data['skills']['skill_count']
        if skills_count < 5:
            suggestions.append({
                'category': 'Skills',
                'priority': 'Critical',
                'suggestion': 'Add more technical skills to your resume. Include programming languages, frameworks, tools, and technologies you have experience with.',
                'impact': 'Significantly improves keyword matching and demonstrates technical competency'
            })
        elif skills_count < 10:
            suggestions.append({
                'category': 'Skills',
                'priority': 'High',
                'suggestion': 'Expand your skills section with more specialized technologies and emerging skills relevant to your field.',
                'impact': 'Helps you stand out for advanced positions and increases ATS matching'
            })
        
        # Experience suggestions
        exp_years = candidate_data['experience']['estimated_years']
        title_count = candidate_data['experience']['title_count']
        
        if exp_years < 2:
            suggestions.append({
                'category': 'Experience',
                'priority': 'High',
                'suggestion': 'Strengthen your experience section by including internships, projects, volunteer work, or part-time roles.',
                'impact': 'Demonstrates practical application of skills and increases experience score'
            })
        
        if title_count < 2:
            suggestions.append({
                'category': 'Experience',
                'priority': 'Medium',
                'suggestion': 'Use more specific job titles and include quantifiable achievements with metrics and numbers.',
                'impact': 'Makes your experience more concrete and measurable for recruiters'
            })
        
        # Education suggestions
        degree_count = candidate_data['education']['degree_count']
        if degree_count == 0:
            suggestions.append({
                'category': 'Education',
                'priority': 'Medium',
                'suggestion': 'Include your educational background, certifications, or relevant coursework.',
                'impact': 'Meets basic educational requirements and improves credibility'
            })
        
        # Content and formatting suggestions
        word_count = candidate_data['summary_stats']['word_count']
        if word_count < 200:
            suggestions.append({
                'category': 'Content',
                'priority': 'Critical',
                'suggestion': 'Expand your resume with more detailed descriptions of your experience and achievements.',
                'impact': 'Provides more context for ATS matching and gives recruiters better insights'
            })
        elif word_count > 800:
            suggestions.append({
                'category': 'Content',
                'priority': 'Low',
                'suggestion': 'Consider condensing your resume to focus on the most relevant and recent experiences.',
                'impact': 'Improves readability and focuses attention on key qualifications'
            })
        
        # Contact information suggestions
        contact_info = candidate_data.get('contact_info', {})
        if not contact_info.get('email'):
            suggestions.append({
                'category': 'Contact Info',
                'priority': 'Critical',
                'suggestion': 'Add a professional email address to your resume.',
                'impact': 'Essential for recruiters to contact you - missing email is a major red flag'
            })
        
        if not contact_info.get('phone'):
            suggestions.append({
                'category': 'Contact Info',
                'priority': 'High',
                'suggestion': 'Include a phone number with proper formatting.',
                'impact': 'Provides additional contact method and shows professionalism'
            })
        
        if not contact_info.get('linkedin'):
            suggestions.append({
                'category': 'Contact Info',
                'priority': 'High',
                'suggestion': 'Include your LinkedIn profile URL.',
                'impact': 'Allows recruiters to see your professional network and endorsements'
            })
        
        # Keyword density analysis
        keyword_data = candidate_data.get('keywords', {})
        unique_words = keyword_data.get('unique_words', 0)
        total_words = keyword_data.get('total_words', 1)
        
        if unique_words / total_words < 0.3:
            suggestions.append({
                'category': 'Keywords',
                'priority': 'Medium',
                'suggestion': 'Use more varied vocabulary and industry-specific terms throughout your resume.',
                'impact': 'Improves matching with diverse job descriptions and shows depth of knowledge'
            })
        
        return suggestions