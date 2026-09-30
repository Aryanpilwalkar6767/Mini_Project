import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Fallback Hugging Face model repository if local weights are missing/not in git
# REPLACE 'YOUR_HF_USERNAME' WITH YOUR ACTUAL HUGGING FACE USERNAME
DEFAULT_HF_MODEL_ID = "https://huggingface.co/Aryan6767/t5-small-informal-to-formal"

class TransformerEngine:
    def __init__(self, model_dir=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_model_path = os.path.join(base_dir, "model", "trained_model")
        
        # Check if local model files exist
        has_local_model = (
            os.path.exists(local_model_path) and 
            os.path.exists(os.path.join(local_model_path, "config.json"))
        )
        
        if has_local_model:
            self.model_identifier = local_model_path
            print(f"[TransformerEngine] Loading model from LOCAL path: {self.model_identifier}")
        else:
            self.model_identifier = os.environ.get("HF_MODEL_ID", DEFAULT_HF_MODEL_ID)
            print(f"[TransformerEngine] Local model not found. Loading from HUGGING FACE: {self.model_identifier}")
            
        self.device = torch.device("cpu")
        
        # Load Tokenizer & Model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_identifier)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_identifier).to(self.device)
        self.model.eval()
        
        print("[TransformerEngine] Model loaded successfully into memory!")

    def generate(self, text: str, max_length: int = 64) -> str:
        if not text or not text.strip():
            return ""
            
        prompt = "formalize: " + text.strip()
        
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=max_length
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=2,
                early_stopping=True
            )
            
        formal_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return formal_text.strip()