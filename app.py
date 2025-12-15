from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import requests

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Video Downloader Backend',
        'version': '1.0'
    })

def extract_youtube_id(url):
    """YouTube video ID'sini çıkar"""
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    elif 'watch?v=' in url:
        return url.split('watch?v=')[1].split('&')[0]
    return None

def try_invidious(video_id):
    """Invidious API ile dene"""
    instances = [
        'https://invidious.snopyta.org',
        'https://yewtu.be',
        'https://vid.puffyan.us',
    ]
    
    for instance in instances:
        try:
            api_url = f'{instance}/api/v1/videos/{video_id}'
            print(f"Trying Invidious: {api_url}")
            
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # En iyi formatı bul
                formats = data.get('formatStreams', [])
                if formats:
                    # MP4 formatını tercih et
                    for fmt in formats:
                        if fmt.get('type', '').startswith('video/mp4'):
                            return {
                                'success': True,
                                'title': data.get('title', 'video'),
                                'url': fmt['url'],
                                'ext': 'mp4'
                            }
                    # Yoksa ilk formatı al
                    return {
                        'success': True,
                        'title': data.get('title', 'video'),
                        'url': formats[0]['url'],
                        'ext': 'mp4'
                    }
        except Exception as e:
            print(f"Invidious {instance} failed: {e}")
            continue
    
    return None

@app.route('/info', methods=['POST'])
def get_info():
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL gerekli'}), 400
        
        # YouTube için Invidious'u dene
        if 'youtube.com' in url or 'youtu.be' in url:
            video_id = extract_youtube_id(url)
            if video_id:
                print(f"YouTube video detected: {video_id}")
                result = try_invidious(video_id)
                if result:
                    print("Invidious success!")
                    return jsonify(result)
                print("Invidious failed, trying yt-dlp...")
        
        # Diğer platformlar için yt-dlp
        ydl_opts = {
            'quiet': False,
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
        }
        
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
                raise Exception("Video URL bulunamadı")
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'video'),
                'url': video_url,
                'ext': info.get('ext', 'mp4')
            })
            
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        
        if 'bot' in error_msg.lower() or 'sign in' in error_msg.lower():
            error_msg = "YouTube bot koruması aktif. Lütfen daha sonra tekrar deneyin."
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)