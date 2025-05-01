from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyotp, qrcode, io, base64
from models import db, User

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///2fa.db'
app.config['SECRET_KEY'] = 'your-very-secret-key-123'  # Change this for production!
db.init_app(app)

# Create database tables
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
            flash('Login successful with 2FA!')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP code')
            return redirect(url_for('verify_2fa'))
    
    return render_template('verify_2fa.html')

# Home route
@app.route('/')
def home():
    return redirect(url_for('login'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)