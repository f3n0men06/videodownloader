from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
from datetime import datetime

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
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # En basit yaklaşım - direkt URL
            video_url = info.get('url')
            
            if not video_url:
                # Formatları kontrol et
                formats = info.get('formats', [])
                if formats:
                    # En iyi formatı bul
                    for f in reversed(formats):
                        if f.get('url'):
                            video_url = f['url']
                            break
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'video'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'url': video_url,
                'ext': info.get('ext', 'mp4')
            })
            
    except Exception as e:
        print(f"Error: {str(e)}")  # Log için
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)