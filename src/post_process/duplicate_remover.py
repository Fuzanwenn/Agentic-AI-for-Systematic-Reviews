"""
Duplicate Remover

This module removes duplicate articles from screening results
and generates final output files with included target articles identified.
"""

import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)


class DuplicateRemover:
    """
    Remove duplicate articles from screening results.
    
    Handles title normalization and deduplication across multiple result files.
    """
    
    def __init__(self, input_dir: Path, output_dir: Path):
        """
        Initialize the duplicate remover.
        
        Args:
            input_dir: Directory containing input files with potential duplicates
            output_dir: Directory where deduplicated files will be written
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DuplicateRemover initialized")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize article title for comparison.
        
        Args:
            title: Raw article title
            
        Returns:
            Normalized title (lowercase, with period at end)
        """
        normalized = title.strip().lower()
        if not normalized.endswith("."):
            normalized += "."
        return normalized
    
    def remove_duplicates(
        self,
        input_files: List[str],
        output_filename: str,
        included_articles: List[str]
    ) -> dict:
        """
        Remove duplicates from multiple input files and create a single output file.
        
        Args:
            input_files: List of input filenames to process
            output_filename: Name of the output file
            included_articles: List of ground truth included articles
            
        Returns:
            Dictionary with processing statistics
        """
        seen_titles: Set[str] = set()
        total_processed = 0
        total_unique = 0
        included_found = []
        
        # Normalize included articles for comparison
        included_set = {self._normalize_title(title) for title in included_articles}
        
        output_path = self.output_dir / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as output_file:
                # Process each input file
                for input_filename in input_files:
                    input_path = self.input_dir / input_filename
                    
                    if not input_path.exists():
                        logger.warning(f"Input file not found: {input_path}")
                        continue
                    
                    logger.info(f"Processing: {input_filename}")
                    
                    with open(input_path, 'r', encoding='utf-8') as input_file:
                        for line in input_file:
                            line = line.strip()
                            
                            # Skip empty lines and metadata
                            if not line or "Total disagreements" in line:
                                continue
                            
                            total_processed += 1
                            
                            # Extract title (before ; or $$$)
                            if ";" in line:
                                raw_title = line.split(";")[0]
                            elif "$$$" in line:
                                raw_title = line.split("$$$")[0]
                            else:
                                raw_title = line
                            
                            normalized_title = self._normalize_title(raw_title)
                            
                            # Check for duplicates
                            if normalized_title not in seen_titles:
                                output_file.write(normalized_title + "\n")
                                seen_titles.add(normalized_title)
                                total_unique += 1
                                
                                # Check if this is an included article
                                if normalized_title in included_set:
                                    included_found.append(normalized_title)
                
                # Add section for included target articles
                output_file.write("\nIncluded target articles are as follow:\n")
                for article in included_found:
                    output_file.write(article + "\n")
            
            stats = {
                "total_processed": total_processed,
                "total_unique": total_unique,
                "duplicates_removed": total_processed - total_unique,
                "included_found": len(included_found),
                "included_articles": included_found,
                "output_file": str(output_path)
            }
            
            logger.info(f"Deduplication complete:")
            logger.info(f"  Total processed: {stats['total_processed']}")
            logger.info(f"  Unique articles: {stats['total_unique']}")
            logger.info(f"  Duplicates removed: {stats['duplicates_removed']}")
            logger.info(f"  Included articles found: {stats['included_found']}")
            logger.info(f"  Output written to: {output_path}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error during deduplication: {e}")
            raise
    
    def batch_remove_duplicates(
        self,
        file_groups: dict,
        included_articles_map: dict
    ) -> dict:
        """
        Remove duplicates from multiple groups of files.
        
        Args:
            file_groups: Dictionary mapping output filenames to lists of input files
            included_articles_map: Dictionary mapping output filenames to included articles
            
        Returns:
            Dictionary with statistics for each output file
        """
        results = {}
        
        for output_filename, input_files in file_groups.items():
            logger.info(f"Processing group: {output_filename}")
            
            included_articles = included_articles_map.get(output_filename, [])
            
            try:
                stats = self.remove_duplicates(
                    input_files,
                    output_filename,
                    included_articles
                )
                results[output_filename] = stats
                
            except Exception as e:
                logger.error(f"Error processing group {output_filename}: {e}")
                results[output_filename] = {"error": str(e)}
        
        return results


def main():
    """Main function for command-line usage."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Duplicate remover module loaded")


if __name__ == "__main__":
    main()
