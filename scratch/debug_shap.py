
import sys
import os
import asyncio
import torch
import numpy as np
import shap

# Add backend to path
sys.path.append(os.path.abspath("backend"))

from app.services.classifier import RoBERTaClassifier
from app.services.explainer import ShapExplainer

async def test():
    classifier = RoBERTaClassifier()
    await classifier.load_model()
    
    explainer = ShapExplainer()
    explainer.initialise(classifier._tokenizer, classifier._model, classifier._device)
    
    text = "pakistan attacks usa"
    print(f"Testing explanation for: {text}")
    try:
        summary, tokens = await explainer.explain(text)
        print(f"Summary: {summary}")
        print(f"Tokens: {tokens}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
