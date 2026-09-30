# FormaLift — Hybrid Informal-to-Formal Text Converter

An intermediate academic NLP mini-project that converts informal English into formal English using a **hybrid architecture**:

1. **Rule-based NLP engine** — deterministic abbreviation, contraction, slang, and formatting normalization  
2. **Fine-tuned T5-small Transformer** — contextual formality / style transfer  
3. **Flask web application** — modern UI with side-by-side comparison of both stages  

> **Design principle:** Rules normalize; the Transformer formalizes; post-processing polishes.

---

## 1. Problem Statement

Informal digital English often contains SMS abbreviations, slang, contractions, elongated characters, and missing punctuation. Simply correcting spelling is not enough. The system must perform **formality style transfer while preserving meaning**.

**Example**

| Stage | Text |
|---|---|
| **Input** | `hey can u send me the report asap? thx` |
| **Rule-based** | `Hey can you send me the report as soon as possible? Thank you` |
| **Hybrid (final)** | `Could you please send me the report as soon as possible? Thank you.` |

---

## 2. Key Features

- Hybrid pipeline: **Rules → T5-small → Post-processing**
- Two visible outputs for academic comparison:
  - Rule-Based Output
  - Hybrid Output (recommended)
- Character & word counters
- Example sentence chips
- Copy / Clear / Download `.txt`
- Browser conversion history (`localStorage`)
- Approximate word-level change highlighting
- Dark / light theme
- Premium UI with glassmorphism + GSAP entrance animations
- Flask REST API
- Deployable on Render (model weights hosted on Hugging Face Hub)

---

## 3. System Architecture

```text
User Input
    │
    ▼
Input Validation & Sanitization
    │
    ▼
┌──────────────────────────────┐
│     Rule-Based Engine        │
│  • abbreviations (u→you)     │
│  • contractions (cant→cannot)│
│  • slang (gonna→going to)    │
│  • repeated chars / punct    │
└──────────────┬───────────────┘
               │
               ├──► Rule-Based Output  ──────────────────► UI
               │
               ▼
┌──────────────────────────────┐
│   Fine-tuned T5-small        │
│   prefix: "formalize: …"     │
│   contextual style rewrite   │
└──────────────┬───────────────┘
               │
               ▼
Lightweight Post-processing
  • capitalize sentence start
  • ensure ending punctuation
  • collapse extra spaces
               │
               └──► Hybrid Output  ──────────────────────► UI
```

### Why this hybrid order (Approach D)?

| Priority | Rationale |
|---|---|
| **Meaning preservation** | Rules only expand known tokens; they do not invent content |
| **Formality** | T5 handles tone, phrasing, and sentence-level rewrite |
| **Reliability** | Deterministic rules catch SMS abbreviations the model may miss |
| **Training/inference match** | Model was fine-tuned on **rule-preprocessed** inputs |

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Deep Learning | PyTorch (CPU inference) |
| NLP / Model | Hugging Face Transformers — **T5-small** (`google-t5/t5-small`) |
| Backend | Flask + Gunicorn |
| Frontend | HTML5, CSS3, Vanilla JavaScript, GSAP |
| Training | Google Colab (GPU) |
| Dataset | Grammarly CoEdIT (formality subset) |
| Model hosting | Hugging Face Hub |
| App hosting | Render (free tier) |

---

## 5. Dataset

### Source
**Grammarly CoEdIT** — `grammarly/coedit` (Hugging Face)  
Paper: *CoEdIT: Text Editing by Task Description* (Raheja et al., 2023)  
License: **Apache 2.0**

### Why this dataset?
- Freely downloadable (no access request, unlike GYAFC / raw XFORMAL data files)
- High-quality human-oriented edits
- Explicit formality-related instructions can be filtered
- Sufficient size for fine-tuning T5-small on Colab

### Processing summary
1. Load CoEdIT from Hugging Face  
2. Filter formality-related examples  
3. Strip instruction prefixes (`Make this text more formal: …`)  
4. Clean: nulls, HTML, URLs, empty strings, extreme lengths, duplicates  
5. Split **80% train / 10% dev / 10% test**  
6. Apply **rule-engine normalization to informal inputs before training** so train-time input matches inference-time hybrid pipeline  

---

## 6. Model

| Item | Choice |
|---|---|
| Base model | `google-t5/t5-small` (~60M parameters) |
| Task framing | `formalize: <rule-normalized informal text>` |
| Max sequence length | 64 tokens (chosen from token-length coverage analysis) |
| Fine-tuning | Hugging Face `Seq2SeqTrainer`, 4 epochs, batch size 32, lr 5e-4 |
| Inference | CPU, beam search (`num_beams=2`) |
| Why T5-small? | Fits free Colab GPU, fast enough for local/CPU web inference, simple prefix-based tasks, appropriate for intermediate academic scope |

---

## 7. Rule-Based Component

Rules live in `rules/informal_rules.json` (not hardcoded in Flask).

**Categories**
- SMS abbreviations: `u → you`, `asap → as soon as possible`, `btw → by the way`
- Contractions: `cant → cannot`, `im → I am`, `dont → do not`
- Slang: `gonna → going to`, `cuz → because`, `wanna → want to`
- Formatting: repeated letters (`soooo → so`), excess punctuation (`!!! → !`)

**Safeguards**
- Whole-word boundary matching (`\b`)
- Case preservation
- Ambiguous single-letter rules handled carefully; complex rewrite deferred to Transformer

**Limitations**
- Cannot restructure sentences or adjust pragmatic tone alone  
- Misses novel slang not in the dictionary  
- Context-blind by design — hence the hybrid architecture  

---

## 8. Project Structure

```text
informal-formal-converter/
│
├── app.py                      # Flask application & REST API
├── requirements.txt
├── render.yaml                 # Render deployment config
├── README.md
├── .gitignore
│
├── model/
│   └── trained_model/          # Local weights (gitignored; HF Hub in production)
│       └── .gitkeep
│
├── rules/
│   └── informal_rules.json     # Rule dictionary
│
├── utils/
│   ├── __init__.py
│   ├── preprocessing.py        # Input validation / sanitization
│   ├── rule_engine.py          # Rule-based transformation
│   ├── transformer_engine.py   # T5 load + generate (local or HF Hub)
│   └── hybrid_pipeline.py      # Orchestrates full pipeline
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/style.css
│   └── js/script.js
│
└── notebooks/
    └── model_training.ipynb    # Colab training reference
```

---

## 9. Local Setup

### Prerequisites
- Python 3.10+
- pip
- ~2 GB free disk for packages + model

### Install

```bash
git clone https://github.com/Aryanpilwalkar6767/231A016_NLP_Experiments/tree/main/AIDS_Sem7_NLP_Mini_Project
cd informal-formal-converter

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir -r requirements.txt
```

### Model weights (local)

Either:

**Option A — Local folder**  
Place fine-tuned files in:

```text
model/trained_model/
  config.json
  generation_config.json
  model.safetensors
  special_tokens_map.json
  spiece.model
  tokenizer.json
  tokenizer_config.json
```

**Option B — Hugging Face Hub**  
Set your repo id in `utils/transformer_engine.py`:

```python
DEFAULT_HF_MODEL_ID = "https://huggingface.co/Aryan6767/t5-small-informal-to-formal"
```

If local weights are missing, the app auto-downloads from HF.

### Run

```bash
python app.py
```

Open: **http://127.0.0.1:5000**

### Quick pipeline unit test

```bash
python -m utils.hybrid_pipeline
```

---

## 10. API Reference

### `GET /api/health`

```json
{
  "status": "healthy",
  "model_loaded": true
}
```

### `POST /api/convert`

**Request**

```json
{
  "text": "hey can u send me the report asap? thx"
}
```

**Success response**

```json
{
  "success": true,
  "original": "hey can u send me the report asap? thx",
  "rule_based": "Hey can you send me the report as soon as possible? Thank you",
  "hybrid": "Could you please send me the report as soon as possible? Thank you.",
  "error": null
}
```

**Error response**

```json
{
  "success": false,
  "original": "",
  "rule_based": "",
  "hybrid": "",
  "error": "Please enter some text to convert."
}
```

---

## 11. Evaluation Methodology

### Automated metrics (test set)
- **BLEU** (SacreBLEU) — n-gram precision vs reference  
- **ROUGE-1 / ROUGE-2 / ROUGE-L** — overlap / longest common subsequence  


| Metric | Rule-Based Only | Hybrid System |
|---|---:|---:|
| BLEU | 10.41 | 15.93 |
| ROUGE-1 | 44.70 | 48.04 |
| ROUGE-2 | 16.98 | 22.46 |
| ROUGE-L | 31.59 | 41.68 |

### Metric limitations for style transfer
- High BLEU/ROUGE ≠ perfect formality; multiple valid formal rewrites exist  
- Meaning preservation is not fully captured by n-gram overlap  
- Therefore a **manual benchmark set** of SMS-heavy sentences is also inspected side-by-side  

---

## 12. Deployment (Render)

1. Upload `model/trained_model/*` to a **public Hugging Face model repo**  
2. Set `DEFAULT_HF_MODEL_ID` (or Render env var `HF_MODEL_ID`)  
3. Push code to GitHub (**do not commit** 200MB+ weight files)  
4. Create a Render **Web Service** from the repo  
5. Build: `pip install -r requirements.txt`  
6. Start: `gunicorn app:app`  
7. Free tier notes:
   - Cold start after idle (~30–60s)
   - CPU only (acceptable for T5-small)
   - First request may download model weights into the instance  

Optional `render.yaml` is included in the repo.

---

## 13. Limitations

1. **Formality is context-dependent** — one “formal” style cannot fit every audience (professor vs client vs official letter).  
2. **Small seq2seq model** — T5-small may underperform large LLMs on creative paraphrase.  
3. **Rule coverage is finite** — unseen slang is left to the Transformer.  
4. **CPU latency** — single conversions typically ~1–3s locally; cold starts slower on free hosting.  
5. **Style-transfer metrics are imperfect** — BLEU/ROUGE must be paired with human inspection.  
6. **English only** in this version.  

---

## 14. Possible Future Improvements

- Controllable formality levels (semi-formal / business / academic)  
- Larger backbone (FLAN-T5-base) if GPU inference is available  
- Multilingual support (mT5 + language-specific rule packs)  
- Toxicity / PII filters before rewrite  
- User feedback loop for active learning  
- Quantized ONNX/runtime build for faster CPU inference  

---

## 15. Requirements

See `requirements.txt`:

```text
flask>=3.0.0
torch>=2.0.0
transformers>=4.38.0
sentencepiece>=0.2.0
gunicorn>=21.2.0
```

Install CPU torch first on limited disks:

```bash
pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir -r requirements.txt
```

---

## 16. References

1. Raffel et al. (2020). *Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer* (T5).  
2. Raheja et al. (2023). *CoEdIT: Text Editing by Task Description*.  
3. Rao & Tetreault (2018). *Dear Sir or Madam, May I Introduce the GYAFC Dataset*.  
4. Briakou et al. (2021). *XFORMAL: A Benchmark for Multilingual Formality Style Transfer*.  
5. Hugging Face Transformers documentation: https://huggingface.co/docs/transformers  
6. Grammarly CoEdIT dataset: https://huggingface.co/datasets/grammarly/coedit  

---

## 17. Author / Academic Info

- **Name:** Aryan Prakash Pilwalkar
- **Project:** Hybrid NLP-Based Informal-to-Formal Text Converter  
- **Course:** NLP Mini Project  
- **Stack:** Rule Engine + Fine-tuned T5-small + Flask  

---

## License

This project code is provided for academic use.  
Dataset: CoEdIT (Apache 2.0).  
Base model: T5 (Apache 2.0).  
Respect third-party licenses when redistributing model weights or data derivatives.


