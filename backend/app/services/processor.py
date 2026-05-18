import asyncio
import logging
from io import BytesIO
import numpy as np
from PIL import Image
import easyocr

from app.services.base import BaseProcessor, OCRResult

logger = logging.getLogger(__name__)

class TesseractProcessor(BaseProcessor):
    """
    Upgraded to EasyOCR but keeping the class name 'TesseractProcessor' 
    so you don't have to change your pipeline.py or main.py.
    """
    def __init__(self, tesseract_cmd=None, language="en"):
        self.language = language
        self.reader = None # Lazy load to save memory

    async def extract_text(self, image_bytes: bytes) -> OCRResult:
        return await asyncio.to_thread(self._extract_sync, image_bytes)

    def _extract_sync(self, image_bytes: bytes) -> OCRResult:
        if self.reader is None:
            # Initialize EasyOCR (uses CPU by default, change gpu=True if you have CUDA)
            self.reader = easyocr.Reader(['en'], gpu=False)

        try:
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            img_np = np.array(image)
            
            # Read text from the image
            results = self.reader.readtext(img_np)
            
            texts = []
            confidences = []
            for (bbox, text, prob) in results:
                if text.strip():
                    texts.append(text)
                    confidences.append(prob)
            
            final_text = "\n".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(f"EasyOCR extracted {len(final_text)} chars, avg confidence: {avg_confidence:.2f}")

            return OCRResult(
                text=final_text,
                language="en",
                confidence=round(avg_confidence, 4),
            )

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            return OCRResult(text="", language="en", confidence=0.0)
