from datetime import datetime
from models import StudentProfile, JobListing
from typing import List, Dict, Tuple

class MatchingEngine:
    """
    Handles intelligent ranking of job listings for students.
    """
    @staticmethod
    def calculate_score(student: StudentProfile, job: JobListing) -> Tuple[float, str]:
        score = 0.0
        reasons = []

        # 1. Skill Overlap (Weighted)
        s_skills = {s.lower() for s in student.skills} if student.skills else set()
        req_skills = {s.lower() for s in job.required_skills} if job.required_skills else set()
        pref_skills = {s.lower() for s in job.preferred_skills} if job.preferred_skills else set()

        req_overlap = len(s_skills.intersection(req_skills))
        pref_overlap = len(s_skills.intersection(pref_skills))

        # Required skills are heavily weighted (e.g., 20 pts each). Preferred are 10 pts.
        score += (req_overlap * 20) + (pref_overlap * 10)
        
        if req_overlap > 0:
            reasons.append(f"Matched {req_overlap} required skills.")

        # 2. Branch/Year Alignment
        if student.graduation_year and job.target_batch:
            if student.graduation_year == job.target_batch:
                score += 30
                reasons.append("Exact graduation year match.")
            elif abs(student.graduation_year - job.target_batch) == 1:
                score += 10 # Minor penalty for being 1 year off

        # 3. Completeness Penalty
        # A 100% complete profile gets 1.0 multiplier. A 40% complete gets 0.4 multiplier.
        completeness = student.completeness_score / 100.0
        score = score * completeness

        # 4. Recency Decay
        # Jobs lose 1 point for every day they've been active
        days_active = (datetime.utcnow() - job.created_at).days
        decay = max(0, days_active * 1.0)
        score -= decay

        # Floor score at 0
        final_score = round(max(0.0, score), 2)
        reason_str = " | ".join(reasons) if reasons else "Partial match based on profile."
        
        return final_score, reason_str

    @classmethod
    def get_ranked_feed(cls, student: StudentProfile, jobs: List[JobListing], limit: int = 10) -> List[Dict]:
        """
        Takes a raw list of ACTIVE jobs from the DB, computes scores in-memory, 
        sorts them, and returns the paginated top results.
        """
        scored_jobs = []
        for job in jobs:
            score, reasoning = cls.calculate_score(student, job)
            scored_jobs.append({
                "job": job,
                "match_score": score,
                "match_reasoning": reasoning
            })

        # Sort descending by score
        scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_jobs[:limit]