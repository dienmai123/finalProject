from crypto_utils import encrypt_message, decrypt_message
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime
from models import db, User  # db comes from models.py
from models import Message

import os, pyotp, qrcode, io, base64

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///2fa.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-default-key-123')

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
    totp_secret = pyotp.random_base32()
    user.totp_secret = totp_secret
    db.session.commit()

    # Generate QR Code
    totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
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

        if user.totp_secret:
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
        totp = pyotp.TOTP(user.totp_secret)

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

            # In a real application, I would send this link via email
            # For demonstration, we'll just show it as a flash message
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

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if not session.get('authenticated'):
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    shared_password = request.form.get('shared_password')
    sender_username = request.form.get('sender_username')
    action = request.form.get('action')

    # Handle Send
    if action == 'send':
        receiver_username = request.form['receiver']
        message_text = request.form['message']

        if not receiver_username or not message_text or not shared_password:
            flash("All fields required to send a message.")
            return redirect(url_for('chat'))

        receiver = User.query.filter_by(username=receiver_username).first()
        if not receiver:
            flash('Receiver does not exist.')
            return redirect(url_for('chat'))

        encrypted = encrypt_message(message_text, shared_password)
        new_msg = Message(sender_id=user.id, receiver_id=receiver.id, ciphertext=encrypted)
        db.session.add(new_msg)
        db.session.commit()
        flash('Message sent securely!', 'chat')
        return redirect(url_for('chat'))

    # Handle Decryption (or just viewing inbox)
    messages_raw = Message.query.filter(
        (Message.sender_id == user.id) | (Message.receiver_id == user.id)
    ).order_by(Message.timestamp.desc()).all()

    sent_messages = []
    received_messages = []
    
    for msg in messages_raw:
        sender_user = User.query.get(msg.sender_id)
        receiver_user = User.query.get(msg.receiver_id)

        message_data = {
            'sender_id': msg.sender_id,
            'receiver_id': msg.receiver_id,
            'sender_username': sender_user.username if sender_user else "Unknown",
            'receiver_username': receiver_user.username if receiver_user else "Unknown",
            'timestamp': msg.timestamp,
            'plaintext': None
        }

        if msg.receiver_id == user.id:  # Received message
            if shared_password and sender_username and sender_username == sender_user.username:
                try:
                    decrypted = decrypt_message(msg.ciphertext, shared_password).decode()
                    message_data['plaintext'] = decrypted
                except Exception:
                    message_data['plaintext'] = "[Decryption failed]"
            else:
                message_data['plaintext'] = "[🔒 Enter shared password and sender username to decrypt]"
            received_messages.append(message_data)
        else:  # Sent message
            message_data['plaintext'] = "[📤 Message sent — content hidden here]"
            sent_messages.append(message_data)

    return render_template("chat.html", 
                         user=user, 
                         sent_messages=sent_messages,
                         received_messages=received_messages)

# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)