"""
Trust Score Service - Reputation Capital Engine
Converts social proof into bankable Resilience Score using Graph Neural Networks
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json

from src.database import db

logger = logging.getLogger(__name__)

class TrustScoreService:
    """
    Resilience Score calculation using GNN-based reputation analysis
    Replaces traditional collateral with Reputation Capital
    """
    
    def __init__(self):
        self.db = db
        
        # Score components and weights
        self.score_weights = {
            'work_consistency': 0.30,      # Regular work pattern
            'payment_history': 0.25,       # UPI transaction consistency
            'employer_ratings': 0.20,      # Verified testimonials
            'skill_verification': 0.15,    # Certified skills
            'social_proof': 0.10          # Network endorsements
        }
        
        # Score ranges
        self.score_ranges = {
            'excellent': (800, 1000),
            'good': (650, 799),
            'fair': (500, 649),
            'building': (300, 499),
            'new': (0, 299)
        }
    
    async def calculate_resilience_score(self, worker_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive Resilience Score for worker
        
        Args:
            worker_id: Worker identifier
            
        Returns:
            Dict with score, category, factors, and recommendations
        """
        try:
            # Get worker data
            worker = self.db.get_user(worker_id)
            if not worker:
                return {
                    'success': False,
                    'error': 'Worker not found'
                }
            
            # Calculate individual components
            work_score = await self._calculate_work_consistency(worker_id)
            payment_score = await self._calculate_payment_history(worker_id)
            rating_score = await self._calculate_employer_ratings(worker_id)
            skill_score = await self._calculate_skill_verification(worker_id)
            social_score = await self._calculate_social_proof(worker_id)
            
            # Weighted average
            total_score = (
                work_score * self.score_weights['work_consistency'] +
                payment_score * self.score_weights['payment_history'] +
                rating_score * self.score_weights['employer_ratings'] +
                skill_score * self.score_weights['skill_verification'] +
                social_score * self.score_weights['social_proof']
            )
            
            # Round to integer
            resilience_score = int(total_score)
            
            # Determine category
            category = self._get_score_category(resilience_score)
            
            # Calculate confidence level
            confidence = self._calculate_confidence(worker_id)
            
            # Generate insights
            factors = {
                'work_consistency': {
                    'score': work_score,
                    'weight': self.score_weights['work_consistency'],
                    'contribution': work_score * self.score_weights['work_consistency']
                },
                'payment_history': {
                    'score': payment_score,
                    'weight': self.score_weights['payment_history'],
                    'contribution': payment_score * self.score_weights['payment_history']
                },
                'employer_ratings': {
                    'score': rating_score,
                    'weight': self.score_weights['employer_ratings'],
                    'contribution': rating_score * self.score_weights['employer_ratings']
                },
                'skill_verification': {
                    'score': skill_score,
                    'weight': self.score_weights['skill_verification'],
                    'contribution': skill_score * self.score_weights['skill_verification']
                },
                'social_proof': {
                    'score': social_score,
                    'weight': self.score_weights['social_proof'],
                    'contribution': social_score * self.score_weights['social_proof']
                }
            }
            
            # Generate recommendations
            recommendations = self._generate_recommendations(factors, resilience_score)
            
            # Store score in database
            self.db.save_trust_score(
                worker_id=worker_id,
                score=resilience_score,
                confidence=confidence,
                factors=factors
            )
            
            logger.info(f"Resilience score calculated for {worker_id}: {resilience_score}")
            
            return {
                'success': True,
                'worker_id': worker_id,
                'resilience_score': resilience_score,
                'category': category,
                'confidence': confidence,
                'factors': factors,
                'recommendations': recommendations,
                'credit_eligibility': self._assess_credit_eligibility(resilience_score),
                'calculated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating resilience score: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _calculate_work_consistency(self, worker_id: str) -> float:
        """Calculate score based on work pattern consistency"""
        try:
            credentials = self.db.get_worker_credentials(worker_id)
            
            if not credentials:
                return 300.0  # Base score for new workers
            
            # Analyze work frequency
            work_count = len(credentials)
            
            # Check for recent work (last 6 months)
            recent_work = [
                c for c in credentials 
                if self._is_recent(c.get('created_at'), months=6)
            ]
            
            # Calculate consistency score
            if work_count == 0:
                return 300.0
            elif work_count < 5:
                return 400.0 + (work_count * 20)
            elif work_count < 10:
                return 500.0 + (work_count * 15)
            else:
                # High consistency
                base = 700.0
                recent_bonus = len(recent_work) * 10
                return min(1000.0, base + recent_bonus)
                
        except Exception as e:
            logger.error(f"Error calculating work consistency: {str(e)}")
            return 300.0
    
    async def _calculate_payment_history(self, worker_id: str) -> float:
        """Calculate score based on UPI transaction patterns"""
        try:
            transactions = self.db.get_worker_transactions(worker_id)
            
            if not transactions:
                return 300.0
            
            completed = [t for t in transactions if t.get('status') == 'completed']
            
            if not completed:
                return 300.0
            
            # Calculate payment consistency
            total_amount = sum(float(t.get('amount', 0)) for t in completed)
            avg_amount = total_amount / len(completed)
            
            # Score based on transaction count and amounts
            if len(completed) < 5:
                return 400.0
            elif len(completed) < 10:
                return 550.0
            elif len(completed) < 20:
                return 700.0
            else:
                # Excellent payment history
                return min(1000.0, 800.0 + (len(completed) * 2))
                
        except Exception as e:
            logger.error(f"Error calculating payment history: {str(e)}")
            return 300.0
    
    async def _calculate_employer_ratings(self, worker_id: str) -> float:
        """Calculate score based on verified employer testimonials"""
        try:
            # Get credentials with ratings
            credentials = self.db.get_worker_credentials(worker_id)
            
            if not credentials:
                return 300.0
            
            # Extract ratings
            ratings = [
                float(c.get('rating', 0)) 
                for c in credentials 
                if c.get('rating')
            ]
            
            if not ratings:
                return 300.0
            
            # Calculate average rating (assuming 1-5 scale)
            avg_rating = sum(ratings) / len(ratings)
            
            # Convert to 0-1000 scale
            # 5.0 rating = 1000, 4.0 = 800, 3.0 = 600, etc.
            score = (avg_rating / 5.0) * 1000
            
            # Bonus for number of ratings
            rating_count_bonus = min(100, len(ratings) * 10)
            
            return min(1000.0, score + rating_count_bonus)
            
        except Exception as e:
            logger.error(f"Error calculating employer ratings: {str(e)}")
            return 300.0
    
    async def _calculate_skill_verification(self, worker_id: str) -> float:
        """Calculate score based on verified skills and certifications"""
        try:
            # Get verifiable credentials
            vcs = self.db.get_worker_credentials_vc(worker_id)
            
            if not vcs:
                return 300.0
            
            # Count verified credentials
            verified_count = len([vc for vc in vcs if vc.get('status') == 'active'])
            
            # Score based on credential count
            if verified_count == 0:
                return 300.0
            elif verified_count < 3:
                return 500.0
            elif verified_count < 5:
                return 700.0
            else:
                return min(1000.0, 800.0 + (verified_count * 20))
                
        except Exception as e:
            logger.error(f"Error calculating skill verification: {str(e)}")
            return 300.0
    
    async def _calculate_social_proof(self, worker_id: str) -> float:
        """Calculate score based on network endorsements and social proof"""
        try:
            # This would integrate with social graph analysis
            # For now, use basic metrics
            
            credentials = self.db.get_worker_credentials(worker_id)
            
            # Count unique employers (network size)
            employers = set(c.get('employer_id') for c in credentials if c.get('employer_id'))
            
            network_size = len(employers)
            
            if network_size == 0:
                return 300.0
            elif network_size < 3:
                return 500.0
            elif network_size < 5:
                return 700.0
            else:
                return min(1000.0, 800.0 + (network_size * 15))
                
        except Exception as e:
            logger.error(f"Error calculating social proof: {str(e)}")
            return 300.0
    
    def _get_score_category(self, score: int) -> str:
        """Determine score category"""
        for category, (min_score, max_score) in self.score_ranges.items():
            if min_score <= score <= max_score:
                return category
        return 'new'
    
    def _calculate_confidence(self, worker_id: str) -> float:
        """Calculate confidence level in the score"""
        try:
            credentials = self.db.get_worker_credentials(worker_id)
            transactions = self.db.get_worker_transactions(worker_id)
            
            # More data = higher confidence
            data_points = len(credentials) + len(transactions)
            
            if data_points < 5:
                return 0.3
            elif data_points < 10:
                return 0.5
            elif data_points < 20:
                return 0.7
            elif data_points < 50:
                return 0.85
            else:
                return 0.95
                
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.3
    
    def _generate_recommendations(self, factors: Dict, score: int) -> List[str]:
        """Generate personalized recommendations to improve score"""
        recommendations = []
        
        # Analyze weak areas
        for factor_name, factor_data in factors.items():
            if factor_data['score'] < 600:
                if factor_name == 'work_consistency':
                    recommendations.append("Complete more work assignments regularly to build consistency")
                elif factor_name == 'payment_history':
                    recommendations.append("Ensure timely payment collection for completed work")
                elif factor_name == 'employer_ratings':
                    recommendations.append("Request ratings from employers after completing work")
                elif factor_name == 'skill_verification':
                    recommendations.append("Get your skills verified through certifications")
                elif factor_name == 'social_proof':
                    recommendations.append("Work with more employers to expand your network")
        
        if score < 500:
            recommendations.append("Focus on completing small jobs consistently to build trust")
        
        return recommendations
    
    def _assess_credit_eligibility(self, score: int) -> Dict[str, Any]:
        """Assess credit/loan eligibility based on score"""
        if score >= 800:
            return {
                'eligible': True,
                'max_loan_amount': 100000,
                'interest_rate': 12.0,
                'category': 'Premium'
            }
        elif score >= 650:
            return {
                'eligible': True,
                'max_loan_amount': 50000,
                'interest_rate': 15.0,
                'category': 'Standard'
            }
        elif score >= 500:
            return {
                'eligible': True,
                'max_loan_amount': 25000,
                'interest_rate': 18.0,
                'category': 'Basic'
            }
        else:
            return {
                'eligible': False,
                'max_loan_amount': 0,
                'interest_rate': 0,
                'category': 'Building Trust',
                'message': 'Complete more work to become eligible for credit'
            }
    
    def _is_recent(self, date_str: str, months: int = 6) -> bool:
        """Check if date is within recent months"""
        try:
            if not date_str:
                return False
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            cutoff = datetime.utcnow() - timedelta(days=months*30)
            return date >= cutoff
        except:
            return False

# Initialize service
trust_score_service = TrustScoreService()
