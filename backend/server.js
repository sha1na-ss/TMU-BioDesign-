/**
 * BECU 2FA Backend - School Project
 * -----------------------------------
 * Stack: Node.js + Express + speakeasy (TOTP) + qrcode
 *
 * Setup:
 *   npm install
 *   node server.js
 *
 * Then open: http://localhost:3000
 */

const express   = require('express');
const cors      = require('cors');
const speakeasy = require('speakeasy');
const QRCode    = require('qrcode');
const path      = require('path');

const app  = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());

// Serve the dashboard folder as static files (relative path — works for everyone)
app.use(express.static(path.join(__dirname, '../dashboard')));

// Serve login.html at the root URL
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../dashboard/login.html'));
});


// ─────────────────────────────────────────────
// In-memory "database" (fine for a school project)
// ─────────────────────────────────────────────
const users = {
  'student': {
    password: 'password123',
    totpSecret: null,
    twoFAEnabled: false
  }
};

const pendingVerifications = {};


// ─────────────────────────────────────────────
// ROUTE 1: POST /api/login
// ─────────────────────────────────────────────
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;

  if (!username || !password)
    return res.json({ success: false, message: 'Username and password are required.' });

  const user = users[username];

  if (!user || user.password !== password)
    return res.json({ success: false, message: 'Invalid username or password.' });

  if (user.twoFAEnabled) {
    pendingVerifications[username] = Date.now();
    return res.json({ success: true, requires2FA: true, username });
  }

  return res.json({ success: true, requires2FA: false, message: 'Login successful!' });
});


// ─────────────────────────────────────────────
// ROUTE 2: POST /api/verify-totp
// ─────────────────────────────────────────────
app.post('/api/verify-totp', (req, res) => {
  const { username, code } = req.body;

  if (!username || !code)
    return res.json({ success: false, message: 'Username and code are required.' });

  const user = users[username];
  if (!user || !user.totpSecret)
    return res.json({ success: false, message: 'User not found or 2FA not configured.' });

  const pending = pendingVerifications[username];
  if (!pending || Date.now() - pending > 5 * 60 * 1000) {
    delete pendingVerifications[username];
    return res.json({ success: false, message: 'Session expired. Please log in again.' });
  }

  const isValid = speakeasy.totp.verify({
    secret:   user.totpSecret,
    encoding: 'base32',
    token:    code,
    window:   1
  });

  if (isValid) {
    delete pendingVerifications[username];
    return res.json({ success: true, message: 'Identity verified! Welcome.' });
  }

  return res.json({ success: false, message: 'Incorrect code. Try again.' });
});


// ─────────────────────────────────────────────
// ROUTE 3: GET /api/setup-2fa?username=student
// Visit this in your browser to get the QR code
// ─────────────────────────────────────────────
app.get('/api/setup-2fa', async (req, res) => {
  const { username } = req.query;

  if (!username || !users[username])
    return res.status(400).json({ success: false, message: 'User not found.' });

  const appName = 'BECU';

  if (!users[username].totpSecret) {
    const secret = speakeasy.generateSecret({ name: appName });
    users[username].totpSecret = secret.base32;
  }

  const secret     = users[username].totpSecret;
  const otpauthUrl = speakeasy.otpauthURL({
    secret:   secret,
    label:    appName,
    encoding: 'base32'
  });

  const qrDataUrl = await QRCode.toDataURL(otpauthUrl);

  users[username].twoFAEnabled = true;

  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>2FA Setup</title>
      <style>
        body { font-family: sans-serif; max-width: 480px; margin: 60px auto; text-align: center; color: #333; }
        h2   { color: #325482; }
        img  { border: 1px solid #ccc; border-radius: 8px; padding: 10px; margin: 20px 0; }
        p    { color: #555; font-size: 0.95rem; line-height: 1.6; }
        a    { color: #325482; font-weight: 600; }
      </style>
    </head>
    <body>
      <h2>🔐 2FA Setup</h2>
      <p>Scan this QR code with <strong>Google Authenticator</strong>:</p>
      <img src="${qrDataUrl}" alt="QR Code" width="220" height="220">
      <p>Once scanned, go back to <a href="http://localhost:3000/login.html">the login page</a>.</p>
    </body>
    </html>
  `);
});


// ─────────────────────────────────────────────
// Start server
// ─────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`\n✅ BECU backend running at http://localhost:${PORT}`);
  console.log(`\n📱 To set up Google Authenticator, visit:`);
  console.log(`   http://localhost:${PORT}/api/setup-2fa?username=student\n`);
});