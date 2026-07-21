import re

VI_SUSPICIOUS = ["tin đồn", "sốc", "kinh hoàng", "bất ngờ", "không thể tin nổi", "tiết lộ", "bí mật", "cú lừa", "sự thật", "tuyệt mật", "chấn động"]
EN_SUSPICIOUS = ["shocking", "unbelievable", "secret", "revealed", "rumor", "banned", "scandal", "miracle", "truth"]

def detect_language(text):
    if not text:
        return 'vi'
    vi_chars = set("áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ")
    text_lower = text.lower()
    vi_count = sum(1 for c in text_lower if c in vi_chars)
    if vi_count > 2 or re.search(r'\b(và|của|là|trong|có|không|người|đã|các)\b', text_lower):
        return 'vi'
    return 'en'

def highlight_suspicious_words(text, lang='vi'):
    suspicious = VI_SUSPICIOUS if lang == 'vi' else EN_SUSPICIOUS
    found = []
    highlighted = text
    
    for word in suspicious:
        pattern = re.compile(rf'\b({word})\b', re.IGNORECASE)
        if pattern.search(highlighted):
            found.append(word)
            highlighted = pattern.sub(r'<span class="suspicious-word">\1</span>', highlighted)
            
    return highlighted, found

def analyze_sentiment(text, lang='vi'):
    negative_vi = ["tệ", "buồn", "chết", "tai nạn", "lừa đảo", "giả dối", "phẫn nộ", "sai phạm", "bức xúc"]
    negative_en = ["bad", "sad", "die", "accident", "scam", "fake", "angry", "violation"]
    
    positive_vi = ["tốt", "vui", "tuyệt vời", "thành công", "hạnh phúc", "phát triển", "tích cực"]
    positive_en = ["good", "happy", "great", "success", "wonderful", "growth", "positive"]
    
    text_lower = text.lower()
    neg_words = negative_vi if lang == 'vi' else negative_en
    pos_words = positive_vi if lang == 'vi' else positive_en
    
    neg_count = sum(1 for w in neg_words if w in text_lower)
    pos_count = sum(1 for w in pos_words if w in text_lower)
    
    if neg_count > pos_count:
        return -0.5 - (min(neg_count, 5) * 0.1), "Tiêu cực" if lang == 'vi' else "Negative"
    elif pos_count > neg_count:
        return 0.5 + (min(pos_count, 5) * 0.1), "Tích cực" if lang == 'vi' else "Positive"
    return 0.0, "Trung lập" if lang == 'vi' else "Neutral"

def get_clickbait_score(title, text, lang='vi'):
    if not title:
        return 0, []
        
    score = 0
    factors = []
    title_lower = title.lower()
    
    if title.endswith('?') or title.endswith('!'):
        score += 25
        factors.append("Tiêu đề chứa dấu câu gây chú ý (!, ?)" if lang == 'vi' else "Title contains attention-grabbing punctuation (!, ?)")
        
    caps_words = [w for w in title.split() if w.isupper() and len(w) > 3]
    if len(caps_words) > 0:
        score += 25
        factors.append("Tiêu đề có chữ IN HOA toàn bộ" if lang == 'vi' else "Title contains ALL CAPS words")
        
    words = title.split()
    if len(words) < 4:
        score += 15
        factors.append("Tiêu đề quá ngắn" if lang == 'vi' else "Title is too short")
    elif len(words) > 20:
        score += 10
        factors.append("Tiêu đề quá dài" if lang == 'vi' else "Title is too long")
        
    cb_vi = ["sốc", "bất ngờ", "kinh hoàng", "sự thật", "tiết lộ", "ngỡ ngàng"]
    cb_en = ["shocking", "unbelievable", "secret", "revealed", "truth"]
    cb_words = cb_vi if lang == 'vi' else cb_en
    
    if any(w in title_lower for w in cb_words):
        score += 35
        factors.append("Tiêu đề chứa từ ngữ giật gân" if lang == 'vi' else "Title contains sensational words")
        
    return min(100, score), factors

def get_source_trust(source):
    if not source:
        return 50, "Không xác định"
        
    source_lower = source.lower()
    
    trusted_domains = ["vnexpress.net", "tuoitre.vn", "thanhnien.vn", "dantri.com.vn", "vtv.vn", "baochinhphu.vn", 
                       "nytimes.com", "bbc.com", "reuters.com", "apnews.com"]
    
    untrusted_domains = ["tinmoi.com", "giatgan.vn", "tinnhanh24h.com"]
    
    for domain in trusted_domains:
        if domain in source_lower:
            return 95, "Độ tin cậy cao"
            
    for domain in untrusted_domains:
        if domain in source_lower:
            return 20, "Độ tin cậy thấp"
            
    return 60, "Độ tin cậy trung bình"

def generate_explanation(prediction, confidence, probs, clickbait_score, source_trust, sentiment, suspicious_words, lang='vi'):
    if lang == 'vi':
        if prediction == 'FAKE':
            explanation = f"Mô hình dự đoán đây là TIN GIẢ với độ tự tin {confidence:.1f}%. "
            if clickbait_score > 60:
                explanation += "Tiêu đề mang tính chất 'giật tít' (clickbait) thu hút sự chú ý. "
            if len(suspicious_words) > 0:
                explanation += f"Văn bản chứa các từ ngữ đáng ngờ thường thấy trong tin giả như: {', '.join(suspicious_words[:3])}. "
        else:
            explanation = f"Mô hình dự đoán đây là TIN THẬT với độ tự tin {confidence:.1f}%. "
            if source_trust > 80:
                explanation += "Nguồn bài báo được xác định là có uy tín và độ tin cậy cao. "
    else:
        if prediction == 'FAKE':
            explanation = f"The model predicts this is FAKE NEWS with {confidence:.1f}% confidence. "
            if clickbait_score > 60:
                explanation += "The title has strong clickbait characteristics. "
            if len(suspicious_words) > 0:
                explanation += f"The text contains suspicious keywords often found in fake news: {', '.join(suspicious_words[:3])}. "
        else:
            explanation = f"The model predicts this is REAL NEWS with {confidence:.1f}% confidence. "
            if source_trust > 80:
                explanation += "The source of the news is highly trusted. "
                
    return explanation
