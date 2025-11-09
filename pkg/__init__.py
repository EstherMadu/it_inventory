import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv
from pkg.models import db

load_dotenv()

csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    from pkg import models
    app = Flask(__name__, instance_relative_config=True, template_folder='templates')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config.from_pyfile("config.py")
    db.init_app(app)
    migrate.init_app(app, db)
    return app


