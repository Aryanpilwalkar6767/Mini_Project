import os
import json
import re

class RuleEngine:
    def __init__(self, rules_filepath=None):
        if rules_filepath is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rules_filepath = os.path.join(base_dir, "rules", "informal_rules.json")
        
        self.rules_filepath = rules_filepath
        self.rules = self._load_rules()
        self.replacement_dict = self._flatten_rules()

    def _load_rules(self):
        """Loads rules from the JSON configuration file."""
        if not os.path.exists(self.rules_filepath):
            raise FileNotFoundError(f"Rule dictionary not found at: {self.rules_filepath}")
        
        with open(self.rules_filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _flatten_rules(self):
        """Combines all rule categories into a single lookup map."""
        flat_dict = {}
        for category in ["abbreviations", "contractions", "slang"]:
            flat_dict.update(self.rules.get(category, {}))
        return flat_dict

    def _preserve_case(self, original_word, replacement_word):
        """Matches the capitalization pattern of the original word."""
        if original_word.isupper():
            return replacement_word.upper()
        elif original_word and original_word[0].isupper():
            return replacement_word.capitalize()
        else:
            return replacement_word.lower()

    def normalize_repeated_chars(self, text):
        """Collapses 3+ repeated characters down to 1 or 2 (e.g., 'sooooo' -> 'so')."""
        # Collapse repeated punctuation first (e.g., "!!!" -> "!", "???" -> "?")
        text = re.sub(r'(!)\1+', r'!', text)
        text = re.sub(r'(\?)\1+', r'?', text)
        text = re.sub(r'(\.)\1{2,}', r'...', text)
        
        # Collapse 3+ repeated letters down to 2 (e.g. 'pleeease' -> 'please')
        text = re.sub(r'([a-zA-Z])\1{2,}', r'\1', text)
        return text

    def apply_word_rules(self, text):
        """Applies word-boundary replacement dictionary to text."""
        for target, replacement in self.replacement_dict.items():
            # Escape target for regex safety (handles contractions with apostrophes)
            pattern = r'\b' + re.escape(target) + r'\b'
            
            def replace_match(match):
                matched_str = match.group(0)
                return self._preserve_case(matched_str, replacement)
            
            text = re.sub(pattern, replace_match, text, flags=re.IGNORECASE)
        return text

    def clean_formatting(self, text):
        """Cleans spacing, punctuation padding, and capitalization."""
        # Normalize double spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure initial character is capitalized
        if text and len(text) > 0:
            text = text[0].upper() + text[1:]
            
        return text

    def transform(self, text):
        """
        Main pipeline method:
        Input Informal Text -> Normalize Chars -> Apply Dictionary Rules -> Format -> Output
        """
        if not text or not text.strip():
            return ""

        # Step 1: Character level normalization
        processed_text = self.normalize_repeated_chars(text)
        
        # Step 2: Dictionary replacement with word boundary matching
        processed_text = self.apply_word_rules(processed_text)
        
        # Step 3: Sentence formatting
        processed_text = self.clean_formatting(processed_text)
        
        return processed_text


# Direct execution test block
if __name__ == "__main__":
    engine = RuleEngine()
    test_samples = [
        "hey can u send me the report asap??? thx",
        "i cant come to the meeting today cuz im sick",
        "im soooo tired rn, wanna reschedule?",
        "btw idk if we gonna finish this on time"
    ]
    
    print("=" * 60)
    print("RULE ENGINE TESTING")
    print("=" * 60)
    for sample in test_samples:
        result = engine.transform(sample)
        print(f"INPUT:  {sample}")
        print(f"OUTPUT: {result}\n")