// utils/db.js
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');

const DB_DIR = path.join(__dirname, '..', 'data');
const DB_PATH = path.join(DB_DIR, 'db.json');

if (!fs.existsSync(DB_DIR)) fs.mkdirSync(DB_DIR, { recursive: true });

function loadDB() {
  if (fs.existsSync(DB_PATH)) return JSON.parse(fs.readFileSync(DB_PATH, 'utf8'));
  return { users: [], updates: [], sessions: [], auditLog: [] };
}
function saveDB(db) { fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2)); }

// ── Users ────────────────────────────────────────────────
function createUser(email, password, name) {
  const db = loadDB();
  const id = uuidv4();
  const licenseKey = `LM-${uuidv4().replace(/-/g, '').toUpperCase().slice(0, 16)}`;
  const user = {
    id, email: email.toLowerCase(), password_hash: bcrypt.hashSync(password, 10),
    name: name || null, license_key: licenseKey, is_paid: 0, purchase_date: null,
    payment_method: null, payment_amount: null, currency: null,
    created_at: new Date().toISOString(), last_login: null, ip_address: null,
  };
  db.users.push(user);
  saveDB(db);
  return { id, email, licenseKey };
}

function getUserByEmail(email) {
  return loadDB().users.find(u => u.email === email.toLowerCase());
}

function getUserById(id) {
  return loadDB().users.find(u => u.id === id);
}

function verifyPassword(user, password) {
  return bcrypt.compareSync(password, user.password_hash);
}

function activateLicense(userId, paymentMethod, amount, currency) {
  const db = loadDB();
  const user = db.users.find(u => u.id === userId);
  if (user) {
    user.is_paid = 1;
    user.purchase_date = new Date().toISOString();
    user.payment_method = paymentMethod;
    user.payment_amount = amount;
    user.currency = currency;
    saveDB(db);
  }
  return user;
}

// ── Sessions ─────────────────────────────────────────────
function createSession(userId, token, expiresAt) {
  const db = loadDB();
  db.sessions.push({ token, user_id: userId, expires_at: expiresAt });
  saveDB(db);
}

function getSession(token) {
  return loadDB().sessions.find(s => s.token === token && new Date(s.expires_at) > new Date());
}

function deleteSession(token) {
  const db = loadDB();
  db.sessions = db.sessions.filter(s => s.token !== token);
  saveDB(db);
}

// ── Updates ──────────────────────────────────────────────
function createUpdate(version, title, description, downloadUrl, checksum) {
  const db = loadDB();
  const id = uuidv4();
  db.updates.push({
    id, version, title, description, download_url: downloadUrl, checksum,
    release_date: new Date().toISOString(), is_active: 0, sent_emails: 0,
  });
  saveDB(db);
  return id;
}

function getActiveUpdates() {
  return loadDB().updates.filter(u => u.is_active === 1).sort((a, b) =>
    new Date(b.release_date).getTime() - new Date(a.release_date).getTime()
  );
}

function getAllUpdates() {
  return loadDB().updates.sort((a, b) =>
    new Date(b.release_date).getTime() - new Date(a.release_date).getTime()
  );
}

function activateUpdate(id) {
  const db = loadDB();
  const u = db.updates.find(u => u.id === id);
  if (u) { u.is_active = 1; saveDB(db); }
}

// ── Stats ────────────────────────────────────────────────
function getStats() {
  const db = loadDB();
  return {
    totalUsers: db.users.length,
    paidUsers: db.users.filter(u => u.is_paid === 1).length,
    totalUpdates: db.updates.length,
  };
}

// ── Audit ────────────────────────────────────────────────
function logAudit(action, userId, ip, details) {
  const db = loadDB();
  db.auditLog.push({
    id: Date.now(), action, user_id: userId || null, ip_address: ip || null,
    details: details || null, created_at: new Date().toISOString(),
  });
  saveDB(db);
}

module.exports = {
  createUser, getUserByEmail, getUserById, verifyPassword, activateLicense,
  createSession, getSession, deleteSession,
  createUpdate, getActiveUpdates, getAllUpdates, activateUpdate,
  getStats, logAudit,
};
