#!/usr/bin/env python3
"""
DeepLog Security Analyzer - Flask Backend
提供Web界面后端API
"""

import json
import os
import sys
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_security_analyzer import EnhancedSecurityAnalyzer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(PROJECT_ROOT, 'frontend', 'dist')
FRONTEND_STATIC = os.path.join(FRONTEND_DIST, 'assets')
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
REPORTS_FOLDER = os.path.join(PROJECT_ROOT, 'reports')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['REPORTS_FOLDER'] = REPORTS_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# Global analyzer instance
analyzer = None

def get_analyzer():
    """Get or create analyzer instance"""
    global analyzer
    if analyzer is None:
        analyzer = EnhancedSecurityAnalyzer()
    return analyzer

# ============== API Routes (must be before catch-all) ==============

@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/analyze', methods=['POST'])
def analyze_logs():
    """Analyze uploaded log file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # Analyze the file
        a = get_analyzer()
        results = a.analyze_file(filepath)

        if not results:
            return jsonify({'error': 'Failed to analyze file'}), 500

        # Generate report
        output_prefix = os.path.join(REPORTS_FOLDER,
                                     f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        a.generate_html_report(results, output_prefix)

        # Extract data from report structure
        total_events = results.get('report_info', {}).get('total_events', 0)
        critical = results.get('threat_level_distribution', {}).get('CRITICAL', 0)
        high = results.get('threat_level_distribution', {}).get('HIGH', 0)
        medium = results.get('threat_level_distribution', {}).get('MEDIUM', 0)
        attack_types = results.get('attack_category_distribution', {})

        # Calculate threat score
        threat_score = min(10, (critical * 3 + high * 1.5 + medium * 0.5) / max(1, total_events / 100))

        return jsonify({
            'success': True,
            'summary': {
                'total_events': total_events,
                'critical': critical,
                'high': high,
                'medium': medium,
                'threat_score': round(threat_score, 1),
                'attack_types': attack_types
            },
            'report_path': f"{output_prefix}.html",
            'detected_events': results.get('critical_events', [])[:20]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quick-analyze', methods=['POST'])
def quick_analyze():
    """Quick analyze pasted log content"""
    data = request.get_json()
    if not data or 'logs' not in data:
        return jsonify({'error': 'No logs provided'}), 400

    try:
        # Save logs to temp file
        temp_file = os.path.join(UPLOAD_FOLDER, 'temp_logs.txt')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(data['logs'])

        a = get_analyzer()
        results = a.analyze_file(temp_file)

        if not results:
            return jsonify({'error': 'Failed to analyze logs'}), 500

        # Extract data from report structure
        total_events = results.get('report_info', {}).get('total_events', 0)
        critical = results.get('threat_level_distribution', {}).get('CRITICAL', 0)
        high = results.get('threat_level_distribution', {}).get('HIGH', 0)
        medium = results.get('threat_level_distribution', {}).get('MEDIUM', 0)
        attack_types = results.get('attack_category_distribution', {})

        # Calculate threat score
        threat_score = min(10, (critical * 3 + high * 1.5 + medium * 0.5) / max(1, total_events / 100))

        return jsonify({
            'success': True,
            'summary': {
                'total_events': total_events,
                'critical': critical,
                'high': high,
                'medium': medium,
                'threat_score': round(threat_score, 1),
                'attack_types': attack_types
            },
            'detected_events': results.get('critical_events', [])[:20]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rules')
def get_rules():
    """Get detection rules info"""
    a = get_analyzer()
    return jsonify({
        'python_rules': len(a.patterns),
        'yaml_rules': len(a.rules),
        'categories': ['sql_injection', 'xss', 'webshell', 'log4j', 'brute_force', 'path_traversal', 'rce']
    })

@app.route('/api/reports')
def list_reports():
    """List available reports"""
    reports = []
    for f in os.listdir(REPORTS_FOLDER):
        if f.endswith('.html'):
            filepath = os.path.join(REPORTS_FOLDER, f)
            reports.append({
                'name': f,
                'path': f'/reports/{f}',
                'size': os.path.getsize(filepath),
                'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
            })
    reports.sort(key=lambda x: x['created'], reverse=True)
    return jsonify(reports)

@app.route('/reports/<path:filename>')
def serve_report(filename):
    """Serve report files"""
    return send_from_directory(REPORTS_FOLDER, filename)

# ============== Static Assets ==============

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve frontend assets"""
    filepath = os.path.join(FRONTEND_STATIC, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({'error': 'Not found'}), 404

# ============== SPA Catch-all (must be last) ==============

@app.route('/')
def index():
    """Serve React frontend"""
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({'error': 'Frontend not built. Run: cd frontend && npm run build'}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 - serve React app for SPA routing"""
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    # Check if frontend is built
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if not os.path.exists(index_path):
        print("=" * 60)
        print("WARNING: React frontend not built!")
        print("Please run: cd frontend && npm run build")
        print("=" * 60)
    else:
        print("=" * 60)
        print("DeepLog Security Analyzer - Web Interface")
        print("=" * 60)
        print("Frontend: Built (production mode)")
        print("=" * 60)

    print("Starting server at http://localhost:5090")
    print("Press Ctrl+C to stop")
    app.run(debug=True, host='0.0.0.0', port=5090)
