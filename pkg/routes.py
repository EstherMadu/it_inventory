import requests
import os, random, json
from flask import current_app as app
from flask import render_template, redirect, flash, request, session
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/')  # Home page route
def home():
    return render_template('index.html')





