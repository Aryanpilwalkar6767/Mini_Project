import os
import gc
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

DEFAULT_HF_MODEL_ID = "Aryan6767/t5-small-informal-to-formal"
FALLBACK_MODEL_ID = "google-t5/t5-small"

class TransformerEngine:
    def __init__(self, model_dir=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_model_path = os.path.join(base_dir, "model", "trained_model")
        
        # Check local model
        has_local_model = (
            os.path.exists(local_model_path) and 
            os.path.exists(os.path.join(local_model_path, "config.json"))
        )
        
        if has_local_model:
            self.model_identifier = local_model_path
            print(f"[TransformerEngine] Loading model from LOCAL path: {self.model_identifier}")
        else:
            raw_id = os.environ.get("HF_MODEL_ID", DEFAULT_HF_MODEL_ID)
            self.model_identifier = (
                raw_id.replace("https://huggingface.co/", "")
                      .replace("http://huggingface.co/", "")
                      .strip("/")
            )
            print(f"[TransformerEngine] Loading from HUGGING FACE: {self.model_identifier}")
            
        self.device = torch.device("cpu")
        
        # Attempt to load model and tokenizer
        try:
            self._load_model_and_tokenizer(self.model_identifier)
        except Exception as e:
            print(f"⚠️ Warning: Failed to load '{self.model_identifier}': {str(e)}")
            print(f"🔄 Falling back to official base model '{FALLBACK_MODEL_ID}'...")
            self.model_identifier = FALLBACK_MODEL_ID
            self._load_model_and_tokenizer(self.model_identifier)

        print("[TransformerEngine] ✅ Model successfully initialized and loaded in memory!")

    def _load_model_and_tokenizer(self, identifier):
        # Clean garbage to free RAM
        gc.collect()
        
        # Load Tokenizer (try fast first, fallback to slow)
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(identifier)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained(identifier, use_fast=False)
            
        # Load Model with memory optimizations for CPU
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            identifier,
            low_cpu_mem_usage=True,
            torch_dtype=torch.float32
        ).to(self.device)
        
        self.model.eval()

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