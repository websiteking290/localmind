// routes/auth.js
const express = require('express');
const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../middleware/auth');
const db = require('../utils/db');

const router = express.Router();

router.post('/register', (req, res) => {
  const { email, password, name } = req.body;
  
  if (!email || !password || password.length < 8) {
    return res.status(400).json({ error: 'Invalid email or password (min 8 chars)' });
  }
  
  if (db.getUserByEmail(email)) {
    return res.status(409).json({ error: 'Email already registered' });
  }
  
  const user = db.createUser(email, password, name);
  res.json({ success: true, user: { id: user.id, email: user.email, licenseKey: user.licenseKey } });
});

router.post('/login', (req, res) => {
  const { email, password } = req.body;
  const user = db.getUserByEmail(email);
  
  if (!user || !db.verifyPassword(user, password)) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  
  const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '7d' });
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
  db.createSession(user.id, token, expiresAt);
  
  res.cookie('token', token, {
    httpOnly: true, secure: true, sameSite: 'lax', maxAge: 7 * 24 * 60 * 60 * 1000,
  });
  
  res.json({
    success: true,
    user: { id: user.id, email: user.email, name: user.name, licenseKey: user.license_key, isPaid: user.is_paid === 1 },
  });
});

router.post('/logout', (req, res) => {
  const token = req.cookies.token;
  if (token) db.deleteSession(token);
  res.clearCookie('token');
  res.json({ success: true });
});

module.exports = router;
