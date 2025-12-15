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
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # En iyi formatı bul
            formats = info.get('formats', [])
            best_format = None
            
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    best_format = f
                    break
            
            if not best_format and formats:
                best_format = formats[-1]
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'video'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'url': best_format.get('url') if best_format else info.get('url'),
                'ext': info.get('ext', 'mp4')
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL gerekli'}), 400
        
        # Geçici dosya
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f'video_{datetime.now().timestamp()}.%(ext)s')
        
        ydl_opts = {
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            return send_file(
                filename,
                as_attachment=True,
                download_name=os.path.basename(filename)
            )
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)