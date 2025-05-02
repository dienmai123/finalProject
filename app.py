from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime
import os, pyotp, qrcode, io, base64

from models import db, User  # db comes from models.py

# Load environment variables from .env
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///2fa.db'
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']  # Load secret key securely

# Register DB with app
db.init_app(app)
migrate = Migrate(app, db)

# Auto-create tables if DB doesn't exist
with app.app_context():
    db.create_all()

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('setup_2fa', username=username))
    
    return render_template('register.html')

# 2FA Setup route
@app.route('/setup_2fa/<username>')
def setup_2fa(username):
    user = User.query.filter_by(username=username).first()
    
    # Generate random secret
    if not user.get_totp_secret():
        totp_secret = pyotp.random_base32()
        user.set_totp_secret(totp_secret)
        db.session.commit()
    else:
        totp_secret = user.get_totp_secret()

    
    # Generate QR Code
    totp_uri = pyotp.TOTP(totp_secret).provisioning_uri(
        name=username,
        issuer_name="Secure 2FA App"
    )
    
    img = qrcode.make(totp_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_code = base64.b64encode(buf.getvalue()).decode('ascii')
    
    return render_template('setup_2fa.html', 
                         qr_code=qr_code, 
                         secret=totp_secret,
                         username=username)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        session['username'] = username
        session['temp_user_id'] = user.id
        
        if user.get_totp_secret():
            return redirect(url_for('verify_2fa'))
        else:
            flash('Login successful (No 2FA enabled)')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# 2FA Verification route
@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['temp_user_id'])
    
    if request.method == 'POST':
        otp = request.form['otp']
        totp = pyotp.TOTP(user.get_totp_secret())
        
        if totp.verify(otp):
            session['authenticated'] = True
            session['user_id'] = user.id
            session.pop('temp_user_id', None)
            
            # Update last login time
            user.last_login = datetime.now()
            db.session.commit()
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP code. Please try again.')
            return redirect(url_for('verify_2fa'))
    
    return render_template('verify_2fa.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    last_login = user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'First login'
    
    return render_template('dashboard.html', 
                         username=user.username,
                         last_login=last_login)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # For demonstration, display the reset link
            reset_link = url_for('reset_password', token=token, _external=True)
            flash(f'Password reset link (for demonstration): {reset_link}')
            return redirect(url_for('forgot_password'))
        
        flash('If a user exists with that username, a password reset link will be sent.')
        return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset link. Please try again.')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('reset_password', token=token))
        
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been reset successfully. Please login with your new password.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
