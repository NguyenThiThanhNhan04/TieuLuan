import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Reconfigure console output encoding to UTF-8 for Windows compatibility
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import crawler
import analyzer
import predictor

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size



def allowed_file(filename):
    """Checks if the uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Renders the main analysis UI."""
    return render_template('index.html', model_mode=config.MODEL_MODE)

@app.route('/dashboard')
def dashboard():
    """Renders the statistics dashboard."""
    return render_template('dashboard.html', model_mode=config.MODEL_MODE)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    Handles news verification requests.
    Supports raw text, URL crawling, and TXT file uploads.
    """
    input_type = request.form.get('type', 'text') # text, url, file
    text_input = ""
    title = "Văn bản nhập trực tiếp"
    source = "Không rõ"
    
    # 1. Gather Input
    if input_type == 'url':
        url = request.form.get('url', '').strip()
        if not url:
            return jsonify({"status": "error", "message": "Vui lòng cung cấp URL bài báo."}), 400
            
        # Crawl the article
        article = crawler.scrape_article(url)
        if 'error' in article:
            return jsonify({"status": "error", "message": article['error']}), 400
            
        title = article['title']
        text_input = f"{article['title']} {article['content']}"
        source = article['source']
        
    elif input_type == 'file':
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "Không tìm thấy tệp tải lên."}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Chưa chọn tệp."}), 400
            
        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Chỉ hỗ trợ tệp định dạng .txt"}), 400
            
        filename = secure_filename(file.filename)
        title = filename
        try:
            text_input = file.read().decode('utf-8', errors='ignore').strip()
        except Exception as e:
            return jsonify({"status": "error", "message": f"Không thể đọc nội dung tệp: {str(e)}"}), 400
            
    else: # Raw text input
        text_input = request.form.get('text', '').strip()
        if not text_input:
            return jsonify({"status": "error", "message": "Vui lòng nhập nội dung tin tức cần phân tích."}), 400
            
    # --- Universal Text Length Validation ---
    if len(text_input) < 100:
        return jsonify({
            "status": "error", 
            "message": "Nội dung quá ngắn (tối thiểu 100 ký tự). Hệ thống AI cần ít nhất 1-2 câu hoàn chỉnh để có thể phân tích chính xác ngữ cảnh và đưa ra kết quả."
        }), 400

    # 2. Detect Language
    lang = analyzer.detect_language(text_input)
    
    # 3. Model Prediction
    try:
        pred_res = predictor.predict(text_input, lang=lang)
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Lỗi trong quá trình chạy mô hình AI: {str(e)}. "
                       f"Hãy thử chuyển MODEL_MODE trong config.py sang 'SVM' để chạy nhẹ nhàng hơn."
        }), 500

    prediction = pred_res['prediction']
    confidence = pred_res['confidence']
    probabilities = pred_res['probabilities']
    model_used = pred_res['model_used']
    
    # 4. Supplementary NLP Analysis
    highlighted_text, suspicious_words = analyzer.highlight_suspicious_words(text_input, lang=lang)
    sentiment_score, sentiment_label = analyzer.analyze_sentiment(text_input, lang=lang)
    clickbait_score, clickbait_factors = analyzer.get_clickbait_score(title, text_input, lang=lang)
    source_trust, source_label = analyzer.get_source_trust(source)
    
    explanation = analyzer.generate_explanation(
        prediction, confidence, probabilities, clickbait_score, source_trust, sentiment_label, suspicious_words, lang=lang
    )

    # 5. Format History Record for Frontend
    history_record = {
        "timestamp": datetime.now().isoformat()[:19],
        "title": title[:100] + ("..." if len(title) > 100 else ""),
        "content_snippet": text_input[:150] + ("..." if len(text_input) > 150 else ""),
        "language": lang,
        "prediction": prediction,
        "confidence": round(confidence, 1),
        "model_used": model_used,
        "source": source,
        "clickbait_score": clickbait_score,
        "sentiment": sentiment_label
    }

    # 6. Return response
    return jsonify({
        "status": "success",
        "data": {
            "prediction": prediction,
            "confidence": confidence,
            "probabilities": probabilities,
            "model_used": model_used,
            "language": lang,
            "title": title,
            "content": text_input,
            "highlighted_content": highlighted_text,
            "suspicious_words": suspicious_words,
            "sentiment": {
                "score": sentiment_score,
                "label": sentiment_label
            },
            "clickbait": {
                "score": clickbait_score,
                "factors": clickbait_factors
            },
            "source": {
                "name": source,
                "trust": source_trust,
                "label": source_label
            },
            "explanation": explanation,
            "history_record": history_record
        }
    })



if __name__ == '__main__':
    # Try creating template and static folders on startup if they don't exist
    os.makedirs(os.path.join(config.BASE_DIR, 'templates'), exist_ok=True)
    os.makedirs(os.path.join(config.BASE_DIR, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(config.BASE_DIR, 'static', 'js'), exist_ok=True)
    
    print("==============================================")
    print("=== STARTING FAKE NEWS DETECTION SYSTEM ===")
    print(f"  Model Mode   : {config.MODEL_MODE}")
    print(f"  PyTorch Device: {predictor.get_device()}")
    print("  Server Address: http://127.0.0.1:5000")
    print("==============================================")
    
    app.run(host='127.0.0.1', port=5000, debug=True)
