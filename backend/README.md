# Backend — 2FA Auth Server

## Install

```bash
npm install
```

## Run

```bash
node server.js
```

Server runs at **http://localhost:3000**

## First-time Setup

Visit this URL to generate your Google Authenticator QR code:

```
http://localhost:3000/api/setup-2fa?username=student
```

Scan the QR code with the **Google Authenticator** app, then log in at **http://localhost:3000**

## Dependencies

- `express` — web server
- `speakeasy` — TOTP code generation and verification
- `qrcode` — QR code generator for 2FA setup
- `cors` — cross-origin request support