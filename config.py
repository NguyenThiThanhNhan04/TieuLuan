import os

# Mode: 'AUTO' (SVM for VI, BERT for EN), 'SVM' (lightweight), or 'TRANSFORMER' (heavy)
MODEL_MODE = 'AUTO'

# Base paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(DATA_DIR, 'models')

# Vietnamese Model Paths
VI_SVM_PATH = os.path.join(MODELS_DIR, 'vietnamese', 'svm_model.pkl')
VI_TFIDF_PATH_NEW = os.path.join(MODELS_DIR, 'vietnamese', 'tfidf.pkl')
VI_TFIDF_PATH_OLD = os.path.join(MODELS_DIR, 'vietnamese', 'tfidf_vectorizer.pkl')
VI_TFIDF_PATH = VI_TFIDF_PATH_NEW if os.path.exists(VI_TFIDF_PATH_NEW) else VI_TFIDF_PATH_OLD

VI_BERT_MODEL_PATH = os.path.join(MODELS_DIR, 'vietnamese', 'bert_model')
VI_BERT_TOKENIZER_PATH = os.path.join(MODELS_DIR, 'vietnamese', 'bert_tokenizer')
VI_LEGACY_TRANSFORMER_PATH = os.path.join(MODELS_DIR, 'vietnamese', 'phobert_model')

# English Model Paths
EN_SVM_PATH = os.path.join(MODELS_DIR, 'english', 'svm_model.pkl')
EN_TFIDF_PATH = os.path.join(MODELS_DIR, 'english', 'tfidf_vectorizer.pkl')
EN_TRANSFORMER_PATH = os.path.join(MODELS_DIR, 'english', 'bert_model')

# App settings
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'txt'}

# Ensure necessary directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
