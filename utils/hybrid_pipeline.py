import os
import re
from utils.preprocessing import validate_and_sanitize_input
from utils.rule_engine import RuleEngine
from utils.transformer_engine import TransformerEngine

class HybridPipeline:
    def __init__(self, rules_path=None, model_dir=None):
        self.rule_engine = RuleEngine(rules_filepath=rules_path)
        self.transformer_engine = TransformerEngine(model_dir=model_dir)

    def _post_process(self, text: str) -> str:
        """
        Lightweight post-processing safety net:
        - Removes double spaces
        - Capitalizes sentence start
        - Ensures valid ending punctuation
        """
        if not text:
            return ""
            
        text = re.sub(r'\s+', ' ', text).strip()
        
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]
            
        if text and text[-1] not in ['.', '!', '?']:
            text += '.'
            
        return text

    def process(self, text: str) -> dict:
        """
        Main execution entry point.
        
        Returns dictionary formatted for Flask response:
        {
            "success": True/False,
            "original": str,
            "rule_based": str,
            "hybrid": str,
            "error": str or None
        }
        """
        # 1. Validation
        val_result = validate_and_sanitize_input(text)
        if not val_result["valid"]:
            return {
                "success": False,
                "original": text or "",
                "rule_based": "",
                "hybrid": "",
                "error": val_result["error"]
            }
            
        original_text = val_result["sanitized_text"]
        
        # 2. Rule-Based Transformation
        rule_output = self.rule_engine.transform(original_text)
        
        # 3. Transformer Neural Rewrite
        raw_transformer_output = self.transformer_engine.generate(rule_output)
        
        # 4. Post-processing
        hybrid_output = self._post_process(raw_transformer_output)
        
        return {
            "success": True,
            "original": original_text,
            "rule_based": rule_output,
            "hybrid": hybrid_output,
            "error": None
        }


# Direct execution test block
if __name__ == "__main__":
    pipeline = HybridPipeline()
    
    test_cases = [
        "hey can u send me the report asap? thx",
        "i cant come to the meeting today cuz im sick",
        "im soooo tired rn, wanna reschedule?",
        "btw idk if we gonna finish this on time"
    ]
    
    print("\n" + "=" * 70)
    print("HYBRID PIPELINE END-TO-END TEST")
    print("=" * 70)
    
    for text in test_cases:
        res = pipeline.process(text)
        print(f"ORIGINAL:   {res['original']}")
        print(f"RULE-BASED: {res['rule_based']}")
        print(f"HYBRID:     {res['hybrid']}")
        print("-" * 70)