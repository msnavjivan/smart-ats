# matching_engine.py - Candidate Matching and Suggestion Engine
import re
from collections import Counter
import math

class MatchingEngine:
    def __init__(self):
        self.weights = {
            'skills_match': 0.4,
            'experience_match': 0.25,
            'education_match': 0.15,
            'keyword_match': 0.2
        }
        
        # Education level hierarchy
        self.education_hierarchy = {
            'high school': 1,
            'diploma': 2,
            'associate': 3,
            'bachelor': 4,
            'master': 5,
            'phd': 6,
            'doctorate': 6
        }
    
    def match_candidates(self, job_data, candidates):
        """Match candidates against a job posting"""
        matches = []
        
        for candidate in candidates:
            match_score = self._calculate_match_score(job_data, candidate['parsed_data'])
            
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
    
    def _calculate_match_score(self, job_data, candidate_data):
        """Calculate comprehensive match score between job and candidate"""
        
        # Skills matching
        skills_score = self._calculate_skills_match(
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
        
        # Keyword matching
        keyword_score = self._calculate_keyword_match(
            job_data.get('description', ''),
            candidate_data.get('raw_text', '')
        )
        
        # Calculate weighted total score
        total_score = (
            skills_score['score'] * self.weights['skills_match'] +
            experience_score['score'] * self.weights['experience_match'] +
            education_score['score'] * self.weights['education_match'] +
            keyword_score['score'] * self.weights['keyword_match']
        )
        
        # Determine strengths and gaps
        strengths = []
        gaps = []
        
        if skills_score['score'] > 0.7:
            strengths.append(f"Strong skills match ({skills_score['matched_skills']} relevant skills)")
        elif skills_score['score'] < 0.3:
            gaps.append(f"Limited skills match (missing {skills_score['missing_skills']} key skills)")
        
        if experience_score['score'] > 0.8:
            strengths.append("Excellent experience level")
        elif experience_score['score'] < 0.4:
            gaps.append("May need more experience")
        
        if education_score['score'] > 0.8:
            strengths.append("Strong educational background")
        elif education_score['score'] < 0.3:
            gaps.append("Education level may not meet requirements")
        
        return {
            'total_score': round(total_score * 100, 2),  # Convert to percentage
            'breakdown': {
                'skills': round(skills_score['score'] * 100, 2),
                'experience': round(experience_score['score'] * 100, 2),
                'education': round(education_score['score'] * 100, 2),
                'keywords': round(keyword_score['score'] * 100, 2)
            },
            'strengths': strengths,
            'gaps': gaps
        }
    
    def _calculate_skills_match(self, required_skills, candidate_skills):
        """Calculate skills matching score"""
        if not required_skills:
            return {'score': 1.0, 'matched_skills': 0, 'missing_skills': 0}
        
        # Normalize skills to lowercase for comparison
        required_lower = [skill.lower().strip() for skill in required_skills]
        candidate_lower = [skill.lower().strip() for skill in candidate_skills]
        
        matched_skills = []
        missing_skills = []
        
        for required_skill in required_lower:
            # Check for exact match or partial match
            matched = False
            for candidate_skill in candidate_lower:
                if (required_skill in candidate_skill or 
                    candidate_skill in required_skill or
                    self._skills_similar(required_skill, candidate_skill)):
                    matched_skills.append(required_skill)
                    matched = True
                    break
            
            if not matched:
                missing_skills.append(required_skill)
        
        match_ratio = len(matched_skills) / len(required_lower) if required_lower else 0
        
        return {
            'score': match_ratio,
            'matched_skills': len(matched_skills),
            'missing_skills': len(missing_skills)
        }
    
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
        """Calculate keyword matching score using TF-IDF-like approach"""
        # Extract important words from job description
        job_words = self._extract_important_words(job_description)
        candidate_words = self._extract_important_words(candidate_text)
        
        if not job_words:
            return {'score': 1.0}
        
        # Calculate overlap
        common_words = set(job_words) & set(candidate_words)
        
        # Weight by frequency in job description
        job_word_freq = Counter(job_words)
        match_score = sum(job_word_freq[word] for word in common_words)
        total_weight = sum(job_word_freq.values())
        
        score = match_score / total_weight if total_weight > 0 else 0
        
        return {'score': min(1.0, score)}
    
    def _extract_important_words(self, text):
        """Extract important words from text (excluding common stop words)"""
        # Simple word extraction and filtering
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Common stop words to exclude
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one',
            'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old',
            'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'will', 'have', 'been', 'that',
            'this', 'with', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time',
            'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such',
            'take', 'than', 'them', 'well', 'were'
        }
        
        # Filter out stop words and short words
        important_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        return important_words
    
    def generate_suggestions(self, candidate_data):
        """Generate improvement suggestions for a candidate"""
        suggestions = []
        
        # Skills suggestions
        skills_count = candidate_data['skills']['skill_count']
        if skills_count < 5:
            suggestions.append({
                'category': 'Skills',
                'priority': 'High',
                'suggestion': 'Add more technical skills to your resume. Include programming languages, tools, and technologies you\'ve worked with.',
                'impact': 'Increases keyword matching and demonstrates technical breadth'
            })
        elif skills_count < 10:
            suggestions.append({
                'category': 'Skills',
                'priority': 'Medium',
                'suggestion': 'Consider adding more specialized or emerging skills relevant to your field.',
                'impact': 'Helps you stand out for advanced positions'
            })
        
        # Experience suggestions
        exp_years = candidate_data['experience']['estimated_years']
        title_count = candidate_data['experience']['title_count']
        
        if exp_years < 2:
            suggestions.append({
                'category': 'Experience',
                'priority': 'High',
                'suggestion': 'Include internships, projects, volunteer work, or part-time roles to demonstrate practical experience.',
                'impact': 'Shows practical application of skills'
            })
        
        if title_count < 2:
            suggestions.append({
                'category': 'Experience',
                'priority': 'Medium',
                'suggestion': 'Use specific job titles and include quantifiable achievements (e.g., "increased efficiency by 20%").',
                'impact': 'Makes your experience more concrete and measurable'
            })
        
        # Education suggestions
        degree_count = candidate_data['education']['degree_count']
        if degree_count == 0:
            suggestions.append({
                'category': 'Education',
                'priority': 'Medium',
                'suggestion': 'Include any formal education, certifications, or relevant coursework.',
                'impact': 'Meets basic educational requirements for most positions'
            })
        
        # Content suggestions
        word_count = candidate_data['summary_stats']['word_count']
        if word_count < 200:
            suggestions.append({
                'category': 'Content',
                'priority': 'High',
                'suggestion': 'Expand your resume with more detailed descriptions of your experience and achievements.',
                'impact': 'Provides more context for ATS matching and recruiter review'
            })
        elif word_count > 800:
            suggestions.append({
                'category': 'Content',
                'priority': 'Low',
                'suggestion': 'Consider condensing your resume to focus on the most relevant and recent experiences.',
                'impact': 'Improves readability and focuses attention on key qualifications'
            })
        
        # Contact information suggestions
        contact_info = candidate_data['contact_info']
        if not contact_info.get('email'):
            suggestions.append({
                'category': 'Contact Info',
                'priority': 'Critical',
                'suggestion': 'Add a professional email address to your resume.',
                'impact': 'Essential for recruiters to contact you'
            })
        
        if not contact_info.get('linkedin'):
            suggestions.append({
                'category': 'Contact Info',
                'priority': 'High',
                'suggestion': 'Include your LinkedIn profile URL to provide more context about your professional background.',
                'impact': 'Allows recruiters to learn more about your network and endorsements'
            })
        
        # Keyword density suggestions
        unique_words = candidate_data['keywords']['unique_words']
        total_words = candidate_data['keywords']['total_words']
        
        if unique_words / total_words < 0.3:
            suggestions.append({
                'category': 'Keywords',
                'priority': 'Medium',
                'suggestion': 'Use more varied vocabulary and industry-specific terms throughout your resume.',
                'impact': 'Improves matching with diverse job descriptions and shows depth of knowledge'
            })
        
        return suggestions