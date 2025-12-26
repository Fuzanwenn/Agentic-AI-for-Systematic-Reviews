"""
Result Matrix Calculator

This module calculates performance metrics for screening results,
including false positives, false negatives, true positives, and true negatives.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Set, Tuple, Dict

logger = logging.getLogger(__name__)


class ScreeningMetricsCalculator:
    """
    Calculate screening performance metrics by comparing results to ground truth.
    """
    
    def __init__(self, dataset_dir: Path, results_dir: Path):
        """
        Initialize the metrics calculator.
        
        Args:
            dataset_dir: Directory containing raw dataset files
            results_dir: Directory containing screening result files
        """
        self.dataset_dir = Path(dataset_dir)
        self.results_dir = Path(results_dir)
        
        if not self.dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {self.dataset_dir}")
        if not self.results_dir.exists():
            raise FileNotFoundError(f"Results directory not found: {self.results_dir}")
        
        logger.info(f"Metrics calculator initialized")
        logger.info(f"Dataset directory: {self.dataset_dir}")
        logger.info(f"Results directory: {self.results_dir}")
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize article title for comparison.
        
        Args:
            title: Article title
            
        Returns:
            Normalized title (lowercase, with period at end)
        """
        normalized = title.strip().lower()
        if not normalized.endswith("."):
            normalized += "."
        return normalized
    
    def _parse_data_file(self, filepath: Path) -> List[str]:
        """
        Parse a data file and extract article titles.
        
        Args:
            filepath: Path to the data file
            
        Returns:
            List of normalized article titles
        """
        titles = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or "Total disagreements" in line:
                        continue
                    
                    # Extract title (before $$$)
                    if "$$$" in line:
                        title = line.split("$$$")[0].strip()
                        titles.append(self._normalize_title(title))
            
            logger.debug(f"Parsed {len(titles)} titles from {filepath.name}")
            return titles
            
        except Exception as e:
            logger.error(f"Error parsing file {filepath}: {e}")
            return []
    
    def get_raw_articles(self, reference_idx: int) -> Tuple[Set[str], int]:
        """
        Get all articles from the raw dataset for a specific reference.
        
        Args:
            reference_idx: Index of the reference (1-based)
            
        Returns:
            Tuple of (set of article titles, total count)
        """
        # Find all data files for this reference
        pattern = f"{reference_idx}_"
        data_files = [
            f for f in self.dataset_dir.iterdir()
            if f.name.startswith(pattern) and f.is_file()
        ]
        
        if not data_files:
            logger.warning(f"No data files found for reference {reference_idx}")
            return set(), 0
        
        all_titles = set()
        total_count = 0
        
        for filepath in data_files:
            titles = self._parse_data_file(filepath)
            total_count += len(titles)
            all_titles.update(titles)
        
        logger.info(
            f"Reference {reference_idx}: {len(all_titles)} unique articles "
            f"({total_count} total)"
        )
        
        return all_titles, total_count
    
    def get_filtered_articles(self, reference_idx: int, 
                             result_filename: str) -> Set[str]:
        """
        Get articles that passed screening for a specific reference.
        
        Args:
            reference_idx: Index of the reference (1-based)
            result_filename: Name of the result file
            
        Returns:
            Set of article titles that passed screening
        """
        filepath = self.results_dir / result_filename
        
        if not filepath.exists():
            logger.warning(f"Result file not found: {filepath}")
            return set()
        
        titles = self._parse_data_file(filepath)
        logger.info(
            f"Reference {reference_idx} filtered results: {len(titles)} articles"
        )
        
        return set(titles)
    
    def calculate_metrics(
        self,
        raw_articles: Set[str],
        filtered_articles: Set[str],
        included_articles: Set[str],
        total_raw: int
    ) -> Dict[str, float]:
        """
        Calculate screening performance metrics.
        
        Args:
            raw_articles: All articles from raw dataset
            filtered_articles: Articles that passed screening
            included_articles: Ground truth included articles
            total_raw: Total count of raw articles
            
        Returns:
            Dictionary with calculated metrics
        """
        # Find included articles in each set
        included_in_raw = raw_articles & included_articles
        included_in_filtered = filtered_articles & included_articles
        
        # Calculate confusion matrix
        tp = len(included_in_filtered)  # Correctly included
        fn = len(included_in_raw - included_in_filtered)  # Incorrectly excluded
        fp = len(filtered_articles - included_articles)  # Incorrectly included
        tn = total_raw - tp - fn - fp  # Correctly excluded
        
        # Calculate rates
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0  # False positive rate
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0  # False negative rate
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0  # Recall
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        metrics = {
            "true_positives": tp,
            "false_negatives": fn,
            "false_positives": fp,
            "true_negatives": tn,
            "total": total_raw,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "precision": precision,
            "missed_articles": list(included_in_raw - included_in_filtered)
        }
        
        logger.info(f"Metrics calculated: TP={tp}, FN={fn}, FP={fp}, TN={tn}")
        logger.info(f"FPR={fpr:.4f}, FNR={fnr:.4f}, Sensitivity={sensitivity:.4f}")
        
        return metrics
    
    def evaluate_reference(
        self,
        reference_idx: int,
        result_filename: str,
        included_articles: List[str]
    ) -> Dict[str, any]:
        """
        Evaluate screening results for a specific reference.
        
        Args:
            reference_idx: Index of the reference (1-based)
            result_filename: Name of the result file
            included_articles: List of ground truth included article titles
            
        Returns:
            Dictionary with evaluation results and metrics
        """
        logger.info(f"Evaluating reference {reference_idx}")
        
        # Normalize included articles
        included_set = {self._normalize_title(title) for title in included_articles}
        
        # Get raw and filtered articles
        raw_articles, total_raw = self.get_raw_articles(reference_idx)
        filtered_articles = self.get_filtered_articles(reference_idx, result_filename)
        
        # Calculate metrics
        metrics = self.calculate_metrics(
            raw_articles, filtered_articles, included_set, total_raw
        )
        
        return {
            "reference_idx": reference_idx,
            "metrics": metrics,
            "raw_count": total_raw,
            "filtered_count": len(filtered_articles),
            "included_count": len(included_set)
        }


def main():
    """Main function for command-line usage."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    # This would normally be called with actual data
    logger.info("Result matrix calculator module loaded")


if __name__ == "__main__":
    main()
