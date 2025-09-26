#!/usr/bin/env python3
"""
JSON Annotation Validator - Flask Web Application
두 JSON/JSONL 파일을 비교하여 변경사항을 분석하는 웹 애플리케이션
"""

import os
import sys
from app import create_app

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = create_app()

if __name__ == '__main__':
    # Get environment variables
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    port = int(os.getenv('PORT', 5000))
    
    # Production/Development server configuration
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )
