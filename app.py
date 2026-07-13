import os
from flask import Flask, request, jsonify, send_file, render_template
from converter import MarkdownToDocx
import markdown as md_lib

app = Flask(__name__)

# Force matplotlib Agg backend before any other import touches it
os.environ.setdefault('MPLBACKEND', 'Agg')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/preview', methods=['POST'])
def preview():
    data = request.get_json()
    md_text = data.get('markdown', '')
    html = md_lib.markdown(md_text, extensions=['extra'])
    return jsonify({'html': html})


@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()
    md_text = data.get('markdown', '')

    converter = MarkdownToDocx()
    docx_buf = converter.convert(md_text)

    return send_file(
        docx_buf,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name='document.docx'
    )


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    if os.environ.get('PRODUCTION', '').lower() in ('1', 'true', 'yes'):
        from waitress import serve
        serve(app, host=host, port=port)
    else:
        app.run(debug=True, host=host, port=port)
