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
        
        # YouTube için özel ayarlar
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
            # Cookie ve user-agent ekle
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Extracting info from: {url}")
            info = ydl.extract_info(url, download=False)
            print(f"Got info: {info.get('title', 'Unknown')}")
            
            # Video URL'sini al
            video_url = None
            
            # Önce direkt URL'yi kontrol et
            if info.get('url'):
                video_url = info['url']
            else:
                # Format listesinden en iyisini bul
                formats = info.get('formats', [])
                # Video+audio içeren formatları önceliklendir
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        if f.get('url'):
                            video_url = f['url']
                            break
                
                # Bulamazsa sadece video formatını al
                if not video_url:
                    for f in formats:
                        if f.get('vcodec') != 'none' and f.get('url'):
                            video_url = f['url']
                            break
            
            if not video_url:
                raise Exception("Video URL bulunamadı")
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'video'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'url': video_url,
                'ext': info.get('ext', 'mp4')
            })
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)