import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import config
import predictor

print("Testing Vietnamese SVM...")
try:
    res_vi_svm = predictor.predict("Đây là tin giả", lang='vi', mode='SVM')
    print("VI SVM SUCCESS:", res_vi_svm)
except Exception as e:
    print("VI SVM FAILED:", e)

print("Testing English SVM...")
try:
    res_en_svm = predictor.predict("This is fake news", lang='en', mode='SVM')
    print("EN SVM SUCCESS:", res_en_svm)
except Exception as e:
    print("EN SVM FAILED:", e)
