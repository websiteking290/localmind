// routes/api.js
const express = require('express');
const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../middleware/auth');
const db = require('../utils/db');

const router = express.Router();

function getUserFromToken(req) {
  const token = req.cookies.token || req.headers.authorization?.replace('Bearer ', '');
  if (!token) return null;
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    return db.getUserById(decoded.userId);
  } catch { return null; }
}

router.get('/user', (req, res) => {
  const user = getUserFromToken(req);
  if (!user) return res.status(401).json({ error: 'Not authenticated' });
  res.json({
    user: {
      id: user.id, email: user.email, name: user.name,
      license_key: user.license_key, is_paid: user.is_paid,
      purchase_date: user.purchase_date,
    },
    updates: db.getActiveUpdates(),
  });
});

router.post('/checkout', (req, res) => {
  const user = getUserFromToken(req);
  if (!user) return res.status(401).json({ error: 'Not authenticated' });
  
  const { method, amount = 129, currency = 'USD' } = req.body;
  
  // Demo mode: activate license immediately
  db.activateLicense(user.id, method || 'demo', amount, currency);
  
  res.json({
    success: true, message: `Payment processed (${method || 'demo'} mode)`,
    licenseKey: user.license_key,
  });
});

router.get('/admin/updates', (req, res) => {
  res.json({ updates: db.getAllUpdates() });
});

router.get('/admin/stats', (req, res) => {
  res.json(db.getStats());
});

router.post('/admin/updates', (req, res) => {
  const { version, title, description, downloadUrl, checksum } = req.body;
  if (!version || !title || !downloadUrl) {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  const id = db.createUpdate(version, title, description, downloadUrl, checksum || '');
  res.json({ success: true, id });
});

router.post('/admin/notify', (req, res) => {
  const { updateId } = req.body;
  const stats = db.getStats();
  console.log(`[EMAIL] Would notify ${stats.paidUsers} paid users about update ${updateId}`);
  res.json({ success: true, message: `Update notification queued for ${stats.paidUsers} paid users (demo mode)`, stats });
});

module.exports = router;
