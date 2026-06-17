import os
import re
import string
import pickle
import unicodedata
import warnings
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import torch
import numpy as np

# Suppress version mismatch warnings during unpickling
warnings.filterwarnings('ignore', category=UserWarning)

# Import config settings
import config

# Initialize NLTK resources safely with a timeout to prevent hanging on network issues
import socket
socket.setdefaulttimeout(5)

for resource in ['stopwords', 'wordnet', 'omw-1.4']:
    try:
        # Check if resource folder exists
        nltk.data.find(f'corpora/{resource}')
    except LookupError:
        try:
            print(f"Đang tải tài nguyên NLTK '{resource}'...")
            nltk.download(resource, quiet=True)
        except Exception as e:
            print(f"Không thể tải tài nguyên NLTK '{resource}': {e}. Ứng dụng vẫn tiếp tục chạy.")

# English NLP Helpers (fallback if NLTK is not fully loaded)
try:
    EN_STOPWORDS = set(stopwords.words('english'))
except Exception:
    EN_STOPWORDS = set()

try:
    EN_LEMMATIZER = WordNetLemmatizer()
except Exception:
    class DummyLemmatizer:
        def lemmatize(self, word): return word
    EN_LEMMATIZER = DummyLemmatizer()

def clean_text_en(text):
    """
    Cleans and normalizes English text (similar to Cell 11 of the English Notebook).
    """
    if not isinstance(text, str):
        return ''
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)   # Remove URLs
    text = re.sub(r'<.*?>', '', text)                       # Remove HTML
    text = re.sub(r'[^a-z\s]', '', text)                   # Remove numbers & special chars
    words = [EN_LEMMATIZER.lemmatize(w) for w in text.split()
             if w not in EN_STOPWORDS and len(w) > 2]
    return ' '.join(words)

# Vietnamese NLP Helpers
from pyvi import ViTokenizer

def clean_text_vi(text):
    """
    Cleans Vietnamese text for TF-IDF / SVM (no word segmentation, similar to Cell 9 of the VI Notebook).
    """
    text = unicodedata.normalize('NFC', str(text)).lower()
    text = re.sub(r'http\S+|www\.\S+', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def clean_and_segment_vi(text):
    """
    Cleans and segments Vietnamese text for PhoBERT / LSTM (using ViTokenizer).
    """
    text = clean_text_vi(text)
    return ViTokenizer.tokenize(text)

# Model Cache
_loaded_models = {}

def get_device():
    """
    Checks if CUDA is available and returns the PyTorch device.
    """
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def load_svm_model(lang):
    """
    Loads SVM model and TF-IDF vectorizer for English or Vietnamese.
    """
    cache_key = f'svm_{lang}'
    if cache_key in _loaded_models:
        return _loaded_models[cache_key]

    if lang == 'vi':
        model_path = config.VI_SVM_PATH
        # Check both path options to be fully robust
        if os.path.exists(config.VI_TFIDF_PATH_NEW):
            tfidf_path = config.VI_TFIDF_PATH_NEW
        elif os.path.exists(config.VI_TFIDF_PATH_OLD):
            tfidf_path = config.VI_TFIDF_PATH_OLD
        else:
            tfidf_path = config.VI_TFIDF_PATH_NEW
    else:
        model_path = config.EN_SVM_PATH
        tfidf_path = config.EN_TFIDF_PATH

    if not os.path.exists(model_path) or not os.path.exists(tfidf_path):
        raise FileNotFoundError(
            f"Không tìm thấy file mô hình SVM ({model_path}) hoặc vectorizer ({tfidf_path}). "
            f"Vui lòng kiểm tra lại đường dẫn."
        )

    with open(tfidf_path, 'rb') as f:
        tfidf = pickle.load(f)
        
    # Version compatibility fix: TfidfTransformer in scikit-learn 1.6+ vs 1.3
    # If the unpickled tfidf object does not have _idf_diag (raising AttributeError/NotFittedError on transform),
    # reconstruct it using the idf_ array found in its internal _tfidf.__dict__
    if hasattr(tfidf, '_tfidf') and 'idf_' in tfidf._tfidf.__dict__:
        import scipy.sparse as sp
        tfidf._tfidf._idf_diag = sp.diags(tfidf._tfidf.__dict__['idf_'])

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    _loaded_models[cache_key] = (tfidf, model)
    return tfidf, model

def load_transformer_model(lang):
    """
    Loads BERT/PhoBERT model and tokenizer for English or Vietnamese.
    """
    cache_key = f'transformer_{lang}'
    if cache_key in _loaded_models:
        return _loaded_models[cache_key]

    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    device = get_device()
    if lang == 'vi':
        # Check for new split PhoBERT directories from notenooks_new
        if os.path.exists(config.VI_BERT_MODEL_PATH) and os.path.exists(config.VI_BERT_TOKENIZER_PATH):
            model_dir = config.VI_BERT_MODEL_PATH
            tokenizer_dir = config.VI_BERT_TOKENIZER_PATH
        else:
            # Fallback to legacy single directory
            model_dir = config.VI_LEGACY_TRANSFORMER_PATH
            tokenizer_dir = config.VI_LEGACY_TRANSFORMER_PATH
    else:
        model_dir = config.EN_TRANSFORMER_PATH
        # English notebook has tokenizer in a separate folder 'bert_tokenizer' next to 'bert_model'
        tokenizer_dir = os.path.join(os.path.dirname(model_dir), 'bert_tokenizer')

    if not os.path.exists(model_dir) or not os.path.exists(tokenizer_dir):
        raise FileNotFoundError(
            f"Không tìm thấy thư mục mô hình Transformer ({model_dir}) hoặc Tokenizer ({tokenizer_dir})."
        )

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device)
    model.eval()

    _loaded_models[cache_key] = (tokenizer, model)
    return tokenizer, model

def predict(text, lang='vi', mode=None):
    """
    Predicts if the text is FAKE or REAL.
    - lang: 'vi' or 'en'
    - mode: 'SVM' or 'TRANSFORMER' (falls back to config.MODEL_MODE if None)
    
    Returns a dictionary:
    {
        "prediction": "REAL" or "FAKE",
        "confidence": float (percentage, e.g., 95.5),
        "probabilities": [prob_real, prob_fake],
        "model_used": str (e.g. "SVM" or "BERT" / "PhoBERT")
    }
    """
    if mode is None:
        mode = config.MODEL_MODE
        
    if mode == 'AUTO':
        mode = 'SVM' if lang == 'vi' else 'TRANSFORMER'

    # Handle fallbacks if Transformer fails to load
    model_used = ""
    try:
        if mode == 'TRANSFORMER':
            model_used = "PhoBERT" if lang == 'vi' else "BERT"
            tokenizer, model = load_transformer_model(lang)
            
            # Preprocess for transformer
            if lang == 'vi':
                processed_text = clean_and_segment_vi(text)
                max_len = 256
            else:
                # English BERT was trained on raw combined text (title + text)
                processed_text = text
                max_len = 128

            device = get_device()
            enc = tokenizer(
                str(processed_text),
                max_length=max_len,
                padding='max_length',
                truncation=True,
                return_attention_mask=True,
                return_token_type_ids=False,
                return_tensors='pt'
            )

            with torch.no_grad():
                ids = enc['input_ids'].to(device)
                mask = enc['attention_mask'].to(device)
                out = model(input_ids=ids, attention_mask=mask)
                logits = out.logits
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
                
            pred_idx = int(np.argmax(probs))
            confidence = float(probs[pred_idx] * 100)
            prob_real = float(probs[0])
            prob_fake = float(probs[1])
            prediction = "FAKE" if pred_idx == 1 else "REAL"

        else: # Default: SVM
            model_used = "SVM"
            tfidf, model = load_svm_model(lang)
            
            # Preprocess for SVM
            if lang == 'vi':
                processed_text = clean_text_vi(text)
            else:
                processed_text = clean_text_en(text)

            X_tfidf = tfidf.transform([processed_text])
            probs = model.predict_proba(X_tfidf)[0]
            pred_idx = int(model.predict(X_tfidf)[0])
            
            confidence = float(probs[pred_idx] * 100)
            prob_real = float(probs[0])
            prob_fake = float(probs[1])
            prediction = "FAKE" if pred_idx == 1 else "REAL"

    except Exception as e:
        # Fallback to SVM if Transformer failed to load or run
        if mode == 'TRANSFORMER':
            print(f"Lỗi khi chạy Transformer ({str(e)}). Tự động chuyển sang chế độ dự phòng SVM...")
            return predict(text, lang=lang, mode='SVM')
        else:
            raise e

    return {
        "prediction": prediction,
        "confidence": confidence,
        "probabilities": [prob_real, prob_fake],
        "model_used": model_used
    }
