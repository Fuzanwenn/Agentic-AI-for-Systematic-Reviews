"""
Metadata Extractor

This module extracts metadata (titles and abstracts) from RIS (Research Information Systems) files,
which are commonly used for exporting bibliographic data from reference management systems.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class RISParser:
    """
    Parse RIS format files to extract article metadata.
    
    RIS format uses specific tags:
    - TI: Title
    - AB: Abstract
    - Other tags may be present but are not currently extracted
    """
    
    def __init__(self):
        """Initialize the RIS parser."""
        self.reset()
    
    def reset(self):
        """Reset parser state."""
        self.current_title = ""
        self.current_abstract = ""
        self.in_title = False
        self.in_abstract = False
    
    def _is_tag_line(self, line: str) -> bool:
        """
        Check if a line contains a RIS tag.
        
        Args:
            line: Line to check
            
        Returns:
            True if line contains a tag pattern like "TI  - " or "AB  - "
        """
        # RIS tags are typically 2 chars followed by spaces and dash
        return "  - " in line or "  -  " in line
    
    def _extract_tag_content(self, line: str, tag: str) -> Optional[str]:
        """
        Extract content from a RIS tag line.
        
        Args:
            line: Line to parse
            tag: Tag to look for (e.g., "TI", "AB")
            
        Returns:
            Content after the tag, or None if tag not found
        """
        # Try different spacing patterns
        for pattern in [f"{tag}  -  ", f"{tag}  - "]:
            if line.strip().startswith(pattern):
                return line.strip().split(pattern, 1)[1]
        return None
    
    def parse_line(self, line: str) -> Optional[Tuple[str, str]]:
        """
        Parse a single line of RIS file.
        
        Args:
            line: Line to parse
            
        Returns:
            Tuple of (title, abstract) if complete entry found, None otherwise
        """
        # Check for title tag
        title_content = self._extract_tag_content(line, "TI")
        if title_content is not None:
            self.current_title = title_content
            self.in_title = True
            self.in_abstract = False
            return None
        
        # Check for abstract tag
        abstract_content = self._extract_tag_content(line, "AB")
        if abstract_content is not None:
            self.current_abstract = abstract_content
            self.in_abstract = True
            self.in_title = False
            return None
        
        # Handle continuation lines (no tag)
        if not self._is_tag_line(line):
            content = line.strip()
            if self.in_title:
                self.current_title += " " + content
            elif self.in_abstract:
                self.current_abstract += " " + content
            return None
        
        # If we hit a new tag and have complete title/abstract
        if self._is_tag_line(line) and self.current_title and self.current_abstract:
            result = (self.current_title, self.current_abstract)
            # Reset for next entry
            self.current_title = ""
            self.current_abstract = ""
            self.in_title = False
            self.in_abstract = False
            return result
        
        # Other tags
        if self.in_title:
            self.in_title = False
        if self.in_abstract:
            self.in_abstract = False
        
        return None
    
    def parse_file(self, filepath: Path) -> List[Tuple[str, str]]:
        """
        Parse a complete RIS file.
        
        Args:
            filepath: Path to the RIS file
            
        Returns:
            List of (title, abstract) tuples
        """
        self.reset()
        entries = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    entry = self.parse_line(line)
                    if entry:
                        entries.append(entry)
                
                # Handle last entry if file doesn't end with a new tag
                if self.current_title and self.current_abstract:
                    entries.append((self.current_title, self.current_abstract))
            
            logger.info(f"Parsed {len(entries)} entries from {filepath.name}")
            return entries
            
        except Exception as e:
            logger.error(f"Error parsing RIS file {filepath}: {e}")
            raise


class MetadataExtractor:
    """
    Extract metadata from RIS files and save in a structured format.
    """
    
    def __init__(self, input_dir: Path, output_dir: Path):
        """
        Initialize the metadata extractor.
        
        Args:
            input_dir: Directory containing RIS files
            output_dir: Directory where extracted metadata will be saved
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.parser = RISParser()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MetadataExtractor initialized")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def extract_from_file(
        self,
        input_filename: str,
        output_filename: Optional[str] = None
    ) -> dict:
        """
        Extract metadata from a single RIS file.
        
        Args:
            input_filename: Name of the input RIS file
            output_filename: Name of the output file (defaults to input name with .txt extension)
            
        Returns:
            Dictionary with extraction statistics
        """
        input_path = self.input_dir / input_filename
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if output_filename is None:
            output_filename = input_path.stem + ".txt"
        
        output_path = self.output_dir / output_filename
        
        logger.info(f"Extracting metadata from: {input_filename}")
        
        # Parse RIS file
        entries = self.parser.parse_file(input_path)
        
        # Write to output file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for title, abstract in entries:
                    f.write(f"{title}$$$ {abstract}\n")
            
            stats = {
                "input_file": str(input_path),
                "output_file": str(output_path),
                "entries_extracted": len(entries)
            }
            
            logger.info(f"Extracted {len(entries)} entries to {output_filename}")
            return stats
            
        except Exception as e:
            logger.error(f"Error writing output file: {e}")
            raise
    
    def batch_extract(self, file_mapping: dict) -> dict:
        """
        Extract metadata from multiple RIS files.
        
        Args:
            file_mapping: Dictionary mapping input filenames to output filenames
            
        Returns:
            Dictionary with statistics for each file
        """
        results = {}
        
        for input_filename, output_filename in file_mapping.items():
            logger.info(f"Processing: {input_filename}")
            
            try:
                stats = self.extract_from_file(input_filename, output_filename)
                results[input_filename] = stats
                
            except Exception as e:
                logger.error(f"Error processing {input_filename}: {e}")
                results[input_filename] = {"error": str(e)}
        
        return results


def main():
    """Main function for command-line usage."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Metadata extractor module loaded")


if __name__ == "__main__":
    main()
