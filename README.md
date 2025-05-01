# 🔒 Secure 2FA Authentication System

A Flask-based two-factor authentication system using TOTP (compatible with Google Authenticator, Authy, etc.).

---

## 🚀 Quick Start

### 1. Install Requirements

```bash
pip install flask pyotp qrcode[pil] flask-sqlalchemy
```

### 2. Initialize the Database

```bash
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 3. Run the Application

```bash
python3 app.py
```

Visit: [http://localhost:5000](http://localhost:5000)

---

## 🔐 How to Test the Login

### First-Time Setup

1. Go to: [http://localhost:5000/register](http://localhost:5000/register)
2. Create a new account
3. Scan the QR code using:
   - Google Authenticator
   - Authy
   - Microsoft Authenticator

### Login Process

1. Go to: [http://localhost:5000/login](http://localhost:5000/login)
2. Enter your username and password
3. Enter the 6-digit TOTP code from your authenticator app

---

## 🛠️ Project Structure

```
2fa_project/
├── app.py                # Main Flask application
├── 2fa.db                # SQLite database (auto-generated)
├── templates/            # HTML templates
│   ├── login.html
│   ├── register.html
│   ├── setup_2fa.html
│   └── verify_2fa.html
```

---

## ❓ Troubleshooting

### "Invalid OTP" Errors

- Ensure your phone's time is synced to network time
- Codes refresh every 30 seconds — try the next code
- Re-scan the QR code if necessary

### Database Issues

If the database is corrupted or missing:

```bash
rm 2fa.db
python3 -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## 🧪 Pro Tip: Generate Test Codes in Python

```python
import pyotp
print(pyotp.TOTP("YOUR_SECRET_KEY").now())  # Replace with the actual secret
```

---

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for more info.

---

## 👤 Author

Dien Mai — mdien2610@gmail.com  
GitHub: [https://github.com/dienmai123](https://github.com/dienmai123)
