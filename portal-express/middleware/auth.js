// middleware/auth.js
const jwt = require('jsonwebtoken');
const db = require('../utils/db');

const JWT_SECRET = process.env.JWT_SECRET || 'localmind-dev-secret-2026';

function requireAuth(req, res, next) {
  const token = req.cookies?.token || req.headers.authorization?.replace('Bearer ', '');
  
  if (!token) return res.redirect('/login');
  
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const user = db.getUserById(decoded.userId);
    if (!user) return res.redirect('/login');
    req.user = user;
    next();
  } catch {
    return res.redirect('/login');
  }
}

function requireAdmin(req, res, next) {
  requireAuth(req, res, () => {
    // For now, any paid user can access admin (demo mode)
    // In production: check req.user.role === 'admin'
    next();
  });
}

module.exports = { requireAuth, requireAdmin, JWT_SECRET };
