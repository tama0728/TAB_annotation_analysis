from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analyzer import JSONAnalyzer

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'jsonl', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'original_file' not in request.files or 'exported_file' not in request.files:
            return jsonify({'error': '두 파일 모두 업로드해주세요.'}), 400
        
        original_file = request.files['original_file']
        exported_file = request.files['exported_file']
        
        if original_file.filename == '' or exported_file.filename == '':
            return jsonify({'error': '파일을 선택해주세요.'}), 400
        
        if not (allowed_file(original_file.filename) and allowed_file(exported_file.filename)):
            return jsonify({'error': 'JSON 또는 JSONL 파일만 업로드 가능합니다.'}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Save uploaded files
        original_filename = secure_filename(original_file.filename)
        exported_filename = secure_filename(exported_file.filename)
        
        original_path = os.path.join(session_dir, f"original_{original_filename}")
        exported_path = os.path.join(session_dir, f"exported_{exported_filename}")
        
        original_file.save(original_path)
        exported_file.save(exported_path)
        
        # Analyze files
        analyzer = JSONAnalyzer()
        report = analyzer.analyze_files(original_path, exported_path)
        
        # Save report
        report_filename = f"report_{session_id}.json"
        report_path = os.path.join(current_app.config['REPORTS_FOLDER'], report_filename)
        analyzer.save_report(report, report_path)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'report_filename': report_filename,
            'summary': {
                'total_records': report['metadata']['total_records'],
                'records_with_changes': report['metadata']['records_with_changes'],
                'text_changes': report['summary']['text_changes'],
                'description_changes': report['summary']['description_changes'],
                'subject_count_changes': report['summary']['subject_count_changes'],
                'pii_annotation_changes': report['summary']['pii_annotation_changes'],
                'data_ids_removed': report['summary'].get('data_ids_removed', 0),
                'data_ids_added': report['summary'].get('data_ids_added', 0)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'분석 중 오류가 발생했습니다: {str(e)}'}), 500

@main.route('/report/<session_id>')
def view_report(session_id):
    report_filename = f"report_{session_id}.json"
    report_path = os.path.join(current_app.config['REPORTS_FOLDER'], report_filename)
    
    if not os.path.exists(report_path):
        flash('보고서를 찾을 수 없습니다.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        import json
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        return render_template('report.html', report=report, session_id=session_id)
    except Exception as e:
        flash(f'보고서 로드 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@main.route('/download/<session_id>')
def download_report(session_id):
    report_filename = f"report_{session_id}.json"
    report_path = os.path.join(os.getcwd(), current_app.config['REPORTS_FOLDER'], report_filename)
    print(report_path)
    print(current_app.config['REPORTS_FOLDER'])
    print(os.getcwd())

    if not os.path.exists(report_path):
        flash('보고서를 찾을 수 없습니다.', 'error')
        # return redirect(url_for('main.index'))
    
    return send_file(report_path, as_attachment=True, download_name=f"analysis_report_{session_id}.json")

@main.route('/api/report/<session_id>')
def api_report(session_id):
    report_filename = f"report_{session_id}.json"
    report_path = os.path.join(current_app.config['REPORTS_FOLDER'], report_filename)
    
    if not os.path.exists(report_path):
        return jsonify({'error': '보고서를 찾을 수 없습니다.'}), 404
    
    try:
        import json
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': f'보고서 로드 중 오류가 발생했습니다: {str(e)}'}), 500
