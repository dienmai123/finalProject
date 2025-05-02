# 🔐 Secure Flask App: 2FA + Encrypted Messaging

This is a Flask-based secure authentication system with:
- TOTP 2FA (e.g., Google Authenticator)
- Encrypted chat via AES-CTR (shared password)
- Password reset with expiring tokens
- Safe `.env` config for secret management
- SQLite database setup on first run

---

## 🚀 Quick Start

### 📦 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/secure-2fa-app.git
cd secure-2fa-app
```

---

### 🔐 2. Environment Configuration

This project includes a pre-configured `.env` file with demo-safe secrets:

```env
SECRET_KEY=dev-secret-key-123
FERNET_KEY=OzH6BeFy8grcF5BXpY0dAixFyJK2xI-3qU9jPlycbKk=
```

> ⚠️ For demo use only. Do not reuse in production.

If your `.env` is missing, run:

```bash
cp .env.example .env
```

---

### 🧰 3. Install Dependencies

```bash
pip install Flask Flask-SQLAlchemy Flask-Migrate python-dotenv pyotp qrcode cryptography
```

---

### 🧠 4. Initialize the Database (only needed if `2fa.db` is missing)

```bash
python app.py
```

This will:
- Auto-create the SQLite DB (`2fa.db`)
- Launch the web app on: [http://localhost:5000](http://localhost:5000)

---

## 🔐 2FA Flow (Google Authenticator)

1. Go to: `/register` and create an account
2. Scan the generated QR code using:
   - Google Authenticator
   - Authy
3. Then go to `/login` and enter:
   - Username and password
   - 6-digit TOTP code from your app

If the TOTP matches, you're logged in.

---

## 💬 Secure Messaging (Encrypted Chat)

1. After logging in, go to `/chat`
2. Use a shared password to:
   - Encrypt outgoing messages
   - Decrypt incoming messages
3. AES-CTR is used with PBKDF2 key derivation for encryption
4. Messages are encrypted end-to-end

> 🔐 The receiver must enter the same password and sender's username to decrypt

---

## 🔁 Password Reset Feature

1. Go to `/forgot-password`
2. Enter your username
3. A reset token is generated (displayed in flash message for demo)
4. Visit the reset link and set a new password

---

## 📂 File Structure

```
.
├── app.py                # Main Flask routes and app logic
├── crypto_utils.py       # AES-CTR encryption utilities
├── models.py             # SQLAlchemy models: User + Message
├── init_db.py            # Rebuild the database
├── update_db.py          # Patch schema with missing columns
├── .env                  # Secret & Fernet keys (demo-safe)
├── .gitignore            # Excludes 2fa.db, __pycache__, etc.
├── templates/            # HTML templates
│   ├── login.html
│   ├── register.html
│   ├── verify_2fa.html
│   ├── setup_2fa.html
│   ├── dashboard.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   └── chat.html
```

---

## 🧪 Troubleshooting

### ❌ OTP Not Working?

- Make sure your phone's time is synced
- TOTP codes refresh every 30s
- Try re-scanning the QR code

### ❌ Decryption Failed?

- Ensure both users enter the **same password**
- Sender's username must be correctly input by receiver
- If decryption fails, message is marked as `[Decryption failed]`

### 💥 DB Error?

```bash
rm 2fa.db
python app.py
```

Or run:

```bash
python init_db.py  # To force rebuild
python update_db.py  # To patch in missing columns
```

---

## 👤 Authors

Dien Mai — mdien2610@gmail.com
GitHub: [https://github.com/dienmai123](https://github.com/dienmai123)

Hoc Nguyen - hocnguyen42804@gmail.com 
GitHub: [https://github.com/HocNguyen123](https://github.com/HocNguyen123)

An Nguyen - 

---

## 📝 License

MIT License — free to use, modify, and learn from.
