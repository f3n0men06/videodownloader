from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Video Downloader Backend',
        'version': '1.0'
    })

@app.route('/info', methods=['POST'])
def get_info():
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL gerekli'}), 400
        
        # Agresif YouTube ayarları
        ydl_opts = {
            'quiet': False,
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
            'extractor_retries': 3,
            'socket_timeout': 30,
            # Bot kontrolünü aşmaya çalış
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        # YouTube için özel
        if 'youtube.com' in url or 'youtu.be' in url:
            # Embed URL'sini dene
            if 'watch?v=' in url:
                video_id = url.split('watch?v=')[1].split('&')[0]
                # Embed URL'si bazen daha az kısıtlama yapar
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                print(f"Trying embed URL: {embed_url}")
                url = embed_url
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Extracting: {url}")
            info = ydl.extract_info(url, download=False)
            
            video_url = info.get('url')
            
            if not video_url:
                formats = info.get('formats', [])
                for f in formats:
                    if f.get('url'):
                        video_url = f['url']
                        break
            
            if not video_url:
                raise Exception("Video URL bulunamadı - YouTube bot kontrolü")
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'video'),
                'url': video_url,
                'ext': info.get('ext', 'mp4')
            })
            
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        
        # YouTube bot kontrolü algıla
        if 'bot' in error_msg.lower() or 'sign in' in error_msg.lower():
            error_msg = "YouTube bot koruması! Bu video şu an indirilemez. Instagram veya TikTok deneyin."
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)