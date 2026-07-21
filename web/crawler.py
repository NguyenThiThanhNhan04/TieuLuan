import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc.lower()

def scrape_article(url):
    """
    Crawls and extracts news article information from a given URL.
    Returns a dictionary with: title, content, author, date, source.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.encoding = response.apparent_encoding or 'utf-8'
        
        if response.status_code != 200:
            return {"error": f"Không thể truy cập trang web (Mã lỗi: {response.status_code})"}
            
        domain = get_domain(url)
        
        # Check if redirected to homepage or search page (article deleted/not found/invalid URL)
        final_url_parsed = urlparse(response.url)
        orig_url_parsed = urlparse(url)
        if final_url_parsed.netloc == orig_url_parsed.netloc and orig_url_parsed.path not in ['', '/']:
            if final_url_parsed.path in ['', '/'] or final_url_parsed.path.startswith('/tim-kiem'):
                return {"error": "URL bài báo không hợp lệ, bị thiếu ký tự hoặc đã bị gỡ bỏ (trang web tự động chuyển hướng)."}

            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = ""
        content = ""
        author = ""
        date = ""
        source = domain.replace('www.', '')
        
        # 1. VnExpress
        if 'vnexpress.net' in domain:
            title_node = soup.select_one('h1.title-detail')
            if title_node:
                title = title_node.text.strip()
                
            desc_node = soup.select_one('p.description')
            desc = desc_node.text.strip() if desc_node else ""
            
            p_nodes = soup.select('p.Normal')
            paragraphs = [p.text.strip() for p in p_nodes if p.text.strip()]
            
            # Extract author if it's the last paragraph
            if paragraphs and len(paragraphs[-1]) < 80:
                author = paragraphs[-1]
                paragraphs = paragraphs[:-1]
                
            content = (desc + "\n" + "\n".join(paragraphs)).strip()
            
            date_node = soup.select_one('span.date')
            if date_node:
                date = date_node.text.strip()

        # 2. Tuổi Trẻ (tuoitre.vn)
        elif 'tuoitre.vn' in domain:
            title_node = soup.select_one('h1.article-title, h1.title-detail')
            if title_node:
                title = title_node.text.strip()
                
            desc_node = soup.select_one('.sapo, .detail-sapo')
            desc = desc_node.text.strip() if desc_node else ""
            
            p_nodes = soup.select('#main-detail-body p, .content p, .fck p')
            paragraphs = [p.text.strip() for p in p_nodes if p.text.strip()]
            
            content = (desc + "\n" + "\n".join(paragraphs)).strip()
            
            date_node = soup.select_one('.date-time, .date')
            if date_node:
                date = date_node.text.strip()

        # 3. Thanh Niên (thanhnien.vn)
        elif 'thanhnien.vn' in domain:
            title_node = soup.select_one('h1.details__title, .details__title, h1.detail-title, .detail-title')
            if title_node:
                title = title_node.text.strip()
                
            desc_node = soup.select_one('.sapo, .detail-sapo')
            desc = desc_node.text.strip() if desc_node else ""
            
            p_nodes = soup.select('.detail-ccontent p, .detail-content p, #main-detail-body p')
            paragraphs = [p.text.strip() for p in p_nodes if p.text.strip()]
            
            content = (desc + "\n" + "\n".join(paragraphs)).strip()
            
            date_node = soup.select_one('.details__meta span, .date')
            if date_node:
                date = date_node.text.strip()

        # 4. Dân Việt (danviet.vn / dan.vn)
        elif 'danviet.vn' in domain or 'dan.vn' in domain:
            title_node = soup.select_one('h1.title, h1.title-detail, h1.detail-title')
            if title_node:
                title = title_node.text.strip()
                
            desc_node = soup.select_one('.sapo, .sapovideo')
            desc = desc_node.text.strip() if desc_node else ""
            
            p_nodes = soup.select('.entry-content p, .detail-content p, .content-detail p')
            paragraphs = [p.text.strip() for p in p_nodes if p.text.strip()]
            
            content = (desc + "\n" + "\n".join(paragraphs)).strip()
            
            date_node = soup.select_one('.date, .datetime')
            if date_node:
                date = date_node.text.strip()
        # 5. AP News (apnews.com)
        elif 'apnews.com' in domain:
            title_node = soup.select_one('h1')
            if title_node:
                title = title_node.text.strip()
                
            # AP News usually puts main content in divs with class RichTextStoryBody
            p_nodes = soup.select('.RichTextStoryBody p, .Page-storyBody p, div[data-key="article"] p')
            paragraphs = []
            for p in p_nodes:
                text = p.text.strip()
                # Loại bỏ các đoạn credit ảnh lặp lại
                if len(text) > 20 and not text.endswith(')'):
                    paragraphs.append(text)
            
            content = "\n".join(paragraphs).strip()
            
            date_node = soup.select_one('time')
            if date_node:
                date = date_node.text.strip()
                
        # 6. Generic Fallback Scraper
        else:
            # B1: Lọc bỏ các thẻ HTML rác (Né rác)
            for tag in soup(["figcaption", "footer", "aside", "nav", "header", "script", "style", "form"]):
                tag.decompose()

            title_node = soup.select_one('h1')
            if title_node:
                title = title_node.text.strip()
                
            # Attempt to gather long paragraphs as content
            p_nodes = soup.select('article p, main p, .content p, p')
            paragraphs = []
            
            # B2: Bộ lọc từ khóa cấm (Blacklist Words)
            blacklist_keywords = ["copyright", "all rights reserved", "photo by", "click here", "subscribe", "newsletter", "advertisement", "sign up"]
            
            for p in p_nodes:
                text = p.text.strip()
                text_lower = text.lower()
                
                # Bỏ qua nếu quá ngắn hoặc chứa từ khóa cấm
                is_spam = any(keyword in text_lower for keyword in blacklist_keywords)
                if len(text) > 40 and not is_spam:
                    paragraphs.append(text)
            
            content = "\n".join(paragraphs[:30]) # cap at 30 paragraphs
            
        # Clean title & content
        title = re.sub(r'\s+', ' ', title).strip()
        content = re.sub(r'\n+', '\n', content).strip()
        
        if not title or not content:
            return {"error": "Không thể trích xuất tiêu đề hoặc nội dung từ URL này. Trang web có thể sử dụng cơ chế chặn hoặc cấu trúc khác."}
            
        return {
            "title": title,
            "content": content,
            "author": author if author else "Không rõ",
            "date": date if date else "Không rõ",
            "source": source
        }
        
    except requests.exceptions.Timeout:
        return {"error": "Kết nối quá thời hạn (Timeout)."}
    except Exception as e:
        return {"error": f"Lỗi không xác định: {str(e)}"}
