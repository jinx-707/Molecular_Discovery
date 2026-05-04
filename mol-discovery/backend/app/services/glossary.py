"""
Scientific Glossary Service
============================
Maintains domain-specific translations for chemistry/biology terms.
Applied before calling general translation APIs to prevent mistranslation.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

log = logging.getLogger(__name__)

# ── Core scientific glossary (English → Kannada) ──────────────────────────
SCIENTIFIC_GLOSSARY: Dict[str, str] = {
    # Molecules & Compounds
    "catalyst": "ವೇಗವರ್ಧಕ",
    "catalysts": "ವೇಗವರ್ಧಕಗಳು",
    "enzyme": "ಕಿಣ್ವ",
    "enzymes": "ಕಿಣ್ವಗಳು",
    "ethanol": "ಇಥೆನಾಲ್",
    "methanol": "ಮೆಥನಾಲ್",
    "methane": "ಮೀಥೇನ್",
    "ammonia": "ಅಮೋನಿಯಾ",
    "hydrogen": "ಹೈಡ್ರೋಜನ್",
    "oxygen": "ಆಮ್ಲಜನಕ",
    "nitrogen": "ಸಾರಜನಕ",
    "carbon dioxide": "ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್",
    "CO2": "CO2",
    "H2": "H2",
    "N2": "N2",
    
    # Properties
    "activity": "ಚಟುವಟಿಕೆ",
    "selectivity": "ಆಯ್ಕೆತೆ",
    "stability": "ಸ್ಥಿರತೆ",
    "thermostability": "ಉಷ್ಣ ಸ್ಥಿರತೆ",
    "uncertainty": "ಅನಿಶ್ಚಿತತೆ",
    "score": "ಅಂಕ",
    "predicted": "ಊಹಿಸಲಾಗಿದೆ",
    "measured": "ಅಳೆಯಲಾಗಿದೆ",
    "temperature": "ತಾಪಮಾನ",
    "pressure": "ಒತ್ತಡ",
    
    # Process terms
    "reaction": "ಪ್ರತಿಕ್ರಿಯೆ",
    "reactions": "ಪ್ರತಿಕ್ರಿಯೆಗಳು",
    "oxidation": "ಆಕ್ಸಿಡೀಕರಣ",
    "reduction": "ಕಡಿತ",
    "synthesis": "ಸಂಶ್ಲೇಷಣೆ",
    "fermentation": "ಹುದುಗುವಿಕೆ",
    "pathway": "ಮಾರ್ಗ",
    "pathways": "ಮಾರ್ಗಗಳು",
    "flux": "ಹರಿವು",
    "yield": "ಇಳುವರಿ",
    
    # Discovery terms
    "discovery": "ಶೋಧನೆ",
    "screening": "ಪರೀಕ್ಷೆ",
    "candidate": "ಅಭ್ಯರ್ಥಿ",
    "candidates": "ಅಭ್ಯರ್ಥಿಗಳು",
    "novel": "ಹೊಸ",
    "known": "ತಿಳಿದಿರುವ",
    "experiment": "ಪ್ರಯೋಗ",
    "experiments": "ಪ್ರಯೋಗಗಳು",
    "model": "ಮಾದರಿ",
    "prediction": "ಮುನ್ಸೂಚನೆ",
    "predictions": "ಮುನ್ಸೂಚನೆಗಳು",
    
    # Fuels
    "jet fuel": "ಜೆಟ್ ಇಂಧನ",
    "biofuel": "ಜೈವಿಕ ಇಂಧನ",
    "biodiesel": "ಜೈವಿಕ ಡೀಸೆಲ್",
    "bioethanol": "ಜೈವಿಕ ಇಥೆನಾಲ್",
    
    # Lab terms
    "researcher": "ಸಂಶೋಧಕ",
    "laboratory": "ಪ್ರಯೋಗಾಲಯ",
    "sample": "ಮಾದರಿ",
    "samples": "ಮಾದರಿಗಳು",
    "data": "ದತ್ತಾಂಶ",
    "results": "ಫಲಿತಾಂಶಗಳು",
    
    # ML/AI terms
    "machine learning": "ಯಂತ್ರ ಕಲಿಕೆ",
    "artificial intelligence": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ",
    "training": "ತರಬೇತಿ",
    "retraining": "ಮರು ತರಬೇತಿ",
    "accuracy": "ನಿಖರತೆ",
    "error": "ದೋಷ",
    "discrepancy": "ವ್ಯತ್ಯಾಸ",
    "drift": "ವಿಚಲನ",
    
    # Genetics/Biology
    "gene": "ಜೀನ್",
    "genes": "ಜೀನ್‌ಗಳು",
    "mutation": "ರೂಪಾಂತರ",
    "mutations": "ರೂಪಾಂತರಗಳು",
    "protein": "ಪ್ರೋಟೀನ್",
    "sequence": "ಅನುಕ್ರಮ",
    "organism": "ಜೀವಿ",
    "microorganism": "ಸೂಕ್ಷ್ಮಜೀವಿ",
}


class GlossaryService:
    """Manages scientific term translations."""
    
    def __init__(self, custom_glossary_path: Optional[Path] = None):
        self.glossary = SCIENTIFIC_GLOSSARY.copy()
        
        # Load custom glossary if provided
        if custom_glossary_path and custom_glossary_path.exists():
            try:
                with open(custom_glossary_path, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
                    self.glossary.update(custom)
                    log.info(f"Loaded {len(custom)} custom glossary entries")
            except Exception as e:
                log.warning(f"Failed to load custom glossary: {e}")
    
    def apply_glossary(self, text: str, source_lang: str = "en", target_lang: str = "kn") -> str:
        """
        Replace scientific terms in text using glossary.
        
        Args:
            text: Input text
            source_lang: Source language code (currently only 'en' supported)
            target_lang: Target language code (currently only 'kn' supported)
        
        Returns:
            Text with glossary terms replaced
        """
        if source_lang != "en" or target_lang != "kn":
            return text  # Only EN→KN supported for now
        
        result = text
        
        # Sort by length (longest first) to handle multi-word terms correctly
        sorted_terms = sorted(self.glossary.items(), key=lambda x: len(x[0]), reverse=True)
        
        for en_term, kn_term in sorted_terms:
            # Case-insensitive replacement
            # Preserve original case for first character if possible
            import re
            pattern = re.compile(re.escape(en_term), re.IGNORECASE)
            result = pattern.sub(kn_term, result)
        
        return result
    
    def get_term(self, english_term: str) -> Optional[str]:
        """Get Kannada translation for a specific English term."""
        return self.glossary.get(english_term.lower())
    
    def add_term(self, english_term: str, kannada_term: str):
        """Add a new term to the glossary (runtime only)."""
        self.glossary[english_term.lower()] = kannada_term
    
    def export_glossary(self, output_path: Path):
        """Export glossary to JSON file for editing."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.glossary, f, ensure_ascii=False, indent=2)
        log.info(f"Exported glossary to {output_path}")
    
    def get_all_terms(self) -> Dict[str, str]:
        """Get all glossary terms."""
        return self.glossary.copy()


# ── Singleton instance ─────────────────────────────────────────────────────
_glossary_service: Optional[GlossaryService] = None


def get_glossary_service() -> GlossaryService:
    """Get or create the global glossary service instance."""
    global _glossary_service
    if _glossary_service is None:
        # Check for custom glossary in backend root
        custom_path = Path(__file__).parent.parent.parent / "glossary_custom.json"
        _glossary_service = GlossaryService(custom_path if custom_path.exists() else None)
    return _glossary_service
