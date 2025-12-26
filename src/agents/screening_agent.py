"""
Two-Tier Screening Agent with Reviewer

This module implements a two-tier screening process for systematic reviews:
1. Classifier tier: Broad categorization (potentially relevant, uncertain, likely irrelevant)
2. Detailed screener tier: PICOS-based evaluation for included/excluded decision

Each tier includes a reviewer-improver loop for quality assurance.
"""

import re
import os
import time
import logging
from typing import Tuple, Optional
from pathlib import Path

from src.llms.chatgpt import gpt_4o_mini, gpt_o3_mini
from config.config import get_config

logger = logging.getLogger(__name__)


class ScreeningMetrics:
    """Track screening metrics and costs."""
    
    def __init__(self):
        self.total_cost = 0.0
        self.total_disagreements = 0
        self.total_processed = 0
    
    def add_cost(self, cost: float):
        """Add to total cost."""
        self.total_cost += cost
    
    def add_disagreement(self):
        """Increment disagreement counter."""
        self.total_disagreements += 1
    
    def increment_processed(self):
        """Increment processed counter."""
        self.total_processed += 1
    
    def get_summary(self) -> dict:
        """Get metrics summary."""
        return {
            "total_cost": self.total_cost,
            "total_disagreements": self.total_disagreements,
            "total_processed": self.total_processed,
            "avg_cost_per_article": self.total_cost / max(self.total_processed, 1)
        }


class CitationClassifier:
    """
    First-tier classifier for broad relevance categorization.
    
    Categorizes articles into: potentially relevant, uncertain, or likely irrelevant.
    """
    
    def __init__(self):
        self.metrics = ScreeningMetrics()
        logger.info("CitationClassifier initialized")
    
    def classify(
        self,
        sr_title: str,
        sr_abstract: str,
        candidate_title: str,
        candidate_abstract: str,
        prompt: str
    ) -> Tuple[str, str]:
        """
        Classify a candidate article's relevance.
        
        Args:
            sr_title: Systematic review title
            sr_abstract: Systematic review abstract
            candidate_title: Candidate article title
            candidate_abstract: Candidate article abstract
            prompt: The prompt to use for classification
            
        Returns:
            Tuple of (justification, decision)
        """
        while True:
            try:
                justification, cost = gpt_4o_mini(prompt, "classifier")
                self.metrics.add_cost(cost)
                
                logger.debug(f"Classifier response: {justification[:100]}...")
                
                if re.search("XXX", justification, re.IGNORECASE):
                    decision = "potentially relevant"
                elif re.search("YYY", justification, re.IGNORECASE):
                    decision = "uncertain"
                elif re.search("ZZZ", justification, re.IGNORECASE):
                    decision = "likely irrelevant"
                else:
                    logger.warning("No valid decision marker found, retrying...")
                    continue
                
                logger.info(f"Classification decision: {decision}")
                return justification, decision
                
            except Exception as e:
                logger.error(f"Error in classification: {e}")
                raise
    
    def review_classification(
        self,
        review_prompt: str
    ) -> Tuple[str, bool]:
        """
        Review a classification decision.
        
        Args:
            review_prompt: The prompt for reviewing
            
        Returns:
            Tuple of (evaluation, agreement)
        """
        while True:
            try:
                evaluation, cost = gpt_o3_mini(review_prompt, "classifier_reviewer")
                self.metrics.add_cost(cost)
                
                logger.debug(f"Reviewer response: {evaluation[:100]}...")
                
                if re.search("XXX", evaluation, re.IGNORECASE):
                    agreement = True
                elif re.search("YYY", evaluation, re.IGNORECASE):
                    agreement = False
                else:
                    logger.warning("No valid agreement marker found, retrying...")
                    continue
                
                logger.info(f"Reviewer agreement: {agreement}")
                return evaluation, agreement
                
            except Exception as e:
                logger.error(f"Error in review: {e}")
                raise
    
    def improve_classification(
        self,
        improver_prompt: str
    ) -> Tuple[str, str]:
        """
        Improve classification based on reviewer feedback.
        
        Args:
            improver_prompt: The prompt for improvement
            
        Returns:
            Tuple of (improved_justification, decision)
        """
        while True:
            try:
                response, cost = gpt_4o_mini(improver_prompt)
                self.metrics.add_cost(cost)
                
                logger.debug(f"Improver response: {response[:100]}...")
                
                if re.search("XXX", response, re.IGNORECASE):
                    decision = "potentially relevant"
                elif re.search("YYY", response, re.IGNORECASE):
                    decision = "uncertain"
                elif re.search("ZZZ", response, re.IGNORECASE):
                    decision = "likely irrelevant"
                else:
                    logger.warning("No valid decision marker found, retrying...")
                    continue
                
                logger.info(f"Improved decision: {decision}")
                return response, decision
                
            except Exception as e:
                logger.error(f"Error in improvement: {e}")
                raise


class DetailedScreener:
    """
    Second-tier detailed screener using PICOS criteria.
    
    Makes final inclusion/exclusion decisions for articles that passed initial screening.
    """
    
    def __init__(self):
        self.metrics = ScreeningMetrics()
        logger.info("DetailedScreener initialized")
    
    def screen(
        self,
        prompt: str
    ) -> Tuple[str, str]:
        """
        Perform detailed PICOS-based screening.
        
        Args:
            prompt: The prompt to use for screening
            
        Returns:
            Tuple of (justification, decision)
        """
        while True:
            try:
                justification, cost = gpt_4o_mini(prompt, "detailed_screener")
                self.metrics.add_cost(cost)
                
                logger.debug(f"Detailed screener response: {justification[:100]}...")
                
                if re.search("YYY", justification, re.IGNORECASE):
                    decision = "included"
                elif re.search("XXX", justification, re.IGNORECASE):
                    decision = "excluded"
                else:
                    logger.warning("No valid decision marker found, retrying...")
                    continue
                
                logger.info(f"Detailed screening decision: {decision}")
                return justification, decision
                
            except Exception as e:
                logger.error(f"Error in detailed screening: {e}")
                raise
    
    def review_screening(
        self,
        review_prompt: str
    ) -> Tuple[str, bool]:
        """
        Review a detailed screening decision.
        
        Args:
            review_prompt: The prompt for reviewing
            
        Returns:
            Tuple of (evaluation, agreement)
        """
        while True:
            try:
                evaluation, cost = gpt_o3_mini(review_prompt, "detailed_screener_reviewer")
                self.metrics.add_cost(cost)
                
                logger.debug(f"Detailed reviewer response: {evaluation[:100]}...")
                
                if re.search("XXX", evaluation, re.IGNORECASE):
                    agreement = True
                elif re.search("YYY", evaluation, re.IGNORECASE):
                    agreement = False
                else:
                    logger.warning("No valid agreement marker found, retrying...")
                    continue
                
                logger.info(f"Detailed reviewer agreement: {agreement}")
                return evaluation, agreement
                
            except Exception as e:
                logger.error(f"Error in detailed review: {e}")
                raise
    
    def improve_screening(
        self,
        improver_prompt: str
    ) -> Tuple[str, str]:
        """
        Improve screening based on reviewer feedback.
        
        Args:
            improver_prompt: The prompt for improvement
            
        Returns:
            Tuple of (improved_justification, decision)
        """
        while True:
            try:
                response, cost = gpt_4o_mini(improver_prompt)
                self.metrics.add_cost(cost)
                
                logger.debug(f"Detailed improver response: {response[:100]}...")
                
                if re.search("XXX", response, re.IGNORECASE):
                    decision = "excluded"
                elif re.search("YYY", response, re.IGNORECASE):
                    decision = "included"
                else:
                    logger.warning("No valid decision marker found, retrying...")
                    continue
                
                logger.info(f"Improved detailed decision: {decision}")
                return response, decision
                
            except Exception as e:
                logger.error(f"Error in detailed improvement: {e}")
                raise


class TwoTierScreeningAgent:
    """
    Main agent coordinating the two-tier screening process.
    
    Note: This implementation requires prompts to be provided by the caller,
    as the prompt templates have been separated from the code for flexibility.
    """
    
    def __init__(self):
        self.classifier = CitationClassifier()
        self.detailed_screener = DetailedScreener()
        self.config = get_config()
        logger.info("TwoTierScreeningAgent initialized")
    
    def get_metrics_summary(self) -> dict:
        """
        Get a summary of all screening metrics.
        
        Returns:
            Dictionary with combined metrics from both tiers
        """
        classifier_metrics = self.classifier.metrics.get_summary()
        detailed_metrics = self.detailed_screener.metrics.get_summary()
        
        total_cost = classifier_metrics["total_cost"] + detailed_metrics["total_cost"]
        total_disagreements = (
            classifier_metrics["total_disagreements"] + 
            detailed_metrics["total_disagreements"]
        )
        
        return {
            "classifier": classifier_metrics,
            "detailed_screener": detailed_metrics,
            "total_cost": total_cost,
            "total_disagreements": total_disagreements
        }
