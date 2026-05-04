"""
Bhashini Translation Client
============================
Wrapper for Government of India's Bhashini translation API.
For hackathon demo: returns mock translations.
For production: implement real API calls with retry logic.
"""
import logging
import os
import time
from typing import Optional, Dict, Any
import httpx

log = logging.getLogger(__name__)

# Bhashini API configuration
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")
BHASHINI_API_URL = os.getenv(
    "BHASHINI_API_URL",
    "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
)

# Demo mode flag
DEMO_MODE = not BHASHINI_API_KEY or os.getenv("TRANSLATION_DEMO_MODE", "true").lower() == "true"


class BhashiniClient:
    """Client for Bhashini translation API."""
    
    def __init__(self, api_key: Optional[str] = None, user_id: Optional[str] = None):
        self.api_key = api_key or BHASHINI_API_KEY
        self.user_id = user_id or BHASHINI_USER_ID
        self.demo_mode = DEMO_MODE
        
        if self.demo_mode:
            log.info("Bhashini client running in DEMO mode (mock translations)")
        else:
            log.info("Bhashini client configured for production API calls")
    
    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "kn",
        timeout: float = 10.0
    ) -> str:
        """
        Translate text using Bhashini API.
        
        Args:
            text: Text to translate
            source_lang: Source language code (ISO 639-1)
            target_lang: Target language code (ISO 639-1)
            timeout: Request timeout in seconds
        
        Returns:
            Translated text
        
        Raises:
            Exception: If translation fails
        """
        if not text or not text.strip():
            return text
        
        # Demo mode: return mock translation
        if self.demo_mode:
            return self._mock_translate(text, source_lang, target_lang)
        
        # Production mode: call Bhashini API
        try:
            return await self._call_bhashini_api(text, source_lang, target_lang, timeout)
        except Exception as e:
            log.error(f"Bhashini API call failed: {e}")
            # Fallback to mock in case of error
            log.warning("Falling back to mock translation")
            return self._mock_translate(text, source_lang, target_lang)
    
    def _mock_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Mock translation for demo purposes.
        Returns a placeholder that indicates translation would happen.
        """
        if source_lang == target_lang:
            return text
        
        # For demo, just add a prefix to show it's "translated"
        # In a real demo, you might use a simple dictionary or Google Translate
        if target_lang == "kn":
            # Return text as-is for demo (glossary already applied)
            # In production, this would be replaced by actual Bhashini call
            return text
        
        return text
    
    async def _call_bhashini_api(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        timeout: float
    ) -> str:
        """
        Call the actual Bhashini API.
        
        Bhashini API documentation:
        https://bhashini.gitbook.io/bhashini-apis/
        """
        if not self.api_key:
            raise ValueError("BHASHINI_API_KEY not configured")
        
        # Prepare request payload
        # Note: Actual payload structure depends on Bhashini API version
        # This is a template - adjust based on official documentation
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        }
                    }
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text
                    }
                ]
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "userID": self.user_id,
            "ulcaApiKey": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                BHASHINI_API_URL,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract translated text from response
            # Adjust based on actual API response structure
            if "pipelineResponse" in data:
                outputs = data["pipelineResponse"][0].get("output", [])
                if outputs:
                    return outputs[0].get("target", text)
            
            log.warning("Unexpected Bhashini API response structure")
            return text
    
    async def translate_batch(
        self,
        texts: list[str],
        source_lang: str = "en",
        target_lang: str = "kn",
        timeout: float = 30.0
    ) -> list[str]:
        """
        Translate multiple texts in batch.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            timeout: Request timeout in seconds
        
        Returns:
            List of translated texts
        """
        # For now, translate one by one
        # TODO: Implement true batch API call if Bhashini supports it
        results = []
        for text in texts:
            try:
                translated = await self.translate(text, source_lang, target_lang, timeout)
                results.append(translated)
            except Exception as e:
                log.error(f"Batch translation failed for text: {e}")
                results.append(text)  # Fallback to original
        
        return results
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported language pairs."""
        # Bhashini supports many Indian languages
        # This is a subset relevant to this project
        return {
            "en": "English",
            "kn": "Kannada (ಕನ್ನಡ)",
            "hi": "Hindi (हिन्दी)",
            "ta": "Tamil (தமிழ்)",
            "te": "Telugu (తెలుగు)",
            "ml": "Malayalam (മലയാളം)",
            "mr": "Marathi (मराठी)",
            "bn": "Bengali (বাংলা)",
            "gu": "Gujarati (ગુજરાતી)",
            "pa": "Punjabi (ਪੰਜਾਬੀ)",
        }


# ── Singleton instance ─────────────────────────────────────────────────────
_bhashini_client: Optional[BhashiniClient] = None


def get_bhashini_client() -> BhashiniClient:
    """Get or create the global Bhashini client instance."""
    global _bhashini_client
    if _bhashini_client is None:
        _bhashini_client = BhashiniClient()
    return _bhashini_client
