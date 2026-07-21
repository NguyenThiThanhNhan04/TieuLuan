# FAKE NEWS DETECTION MODELS (ENGLISH - 22K)
- lstm_model.keras

## Dataset
- Source: WELFake Dataset (English)
- Total: 22,054 samples (balanced with Vietnamese dataset)
- Real (0): 15,886 (72%)
- Fake (1): 6,168 (28%)
- Split: Train 70% | Val 15% | Test 15%

## Models
1. Random Forest + TF-IDF
2. SVM + TF-IDF
3. LSTM (Keras)
4. BERT (bert-base-uncased)

## Files
- tfidf_vectorizer.pkl
- random_forest.pkl
- svm_model.pkl

- lstm_tokenizer.pkl
- bert_model/
- bert_tokenizer/
