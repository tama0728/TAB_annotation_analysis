from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['UPLOAD_FOLDER'] = 'app/uploads'
    app.config['REPORTS_FOLDER'] = 'app/reports'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload and reports directories exist
    # os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER']), exist_ok=True)
    os.makedirs(os.path.join(os.getcwd(), app.config['REPORTS_FOLDER']), exist_ok=True)
    
    from app.routes import main
    app.register_blueprint(main)
    
    return app
