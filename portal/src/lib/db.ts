// src/lib/db.ts
// Simple JSON-based database for LocalMind portal (swap for SQLite in production)
import { v4 as uuidv4 } from 'uuid';
import bcrypt from 'bcryptjs';
import fs from 'fs';
import path from 'path';

const DB_PATH = '/Users/sam/workspace/usb-ai-sales/portal/data/db.json';

// Ensure data directory exists
const dataDir = path.dirname(DB_PATH);
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

// Load or init DB
function loadDB(): any {
  if (fs.existsSync(DB_PATH)) {
    return JSON.parse(fs.readFileSync(DB_PATH, 'utf8'));
  }
  return { users: [], updates: [], sessions: [], auditLog: [] };
}

function saveDB(db: any) {
  fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2));
}

// ── User Operations ────────────────────────────────────────
export function createUser(email: string, password: string, name?: string) {
  const db = loadDB();
  const id = uuidv4();
  const licenseKey = `LM-${uuidv4().replace(/-/g, '').toUpperCase().slice(0, 16)}`;
  const hash = bcrypt.hashSync(password, 10);
  
  const user = {
    id, email: email.toLowerCase(), password_hash: hash, name: name || null,
    license_key: licenseKey, is_paid: 0, purchase_date: null,
    payment_method: null, payment_amount: null, currency: null,
    created_at: new Date().toISOString(), last_login: null, ip_address: null,
  };
  
  db.users.push(user);
  saveDB(db);
  return { id, email, licenseKey };
}

export function getUserByEmail(email: string) {
  const db = loadDB();
  return db.users.find((u: any) => u.email === email.toLowerCase());
}

export function getUserById(id: string) {
  const db = loadDB();
  return db.users.find((u: any) => u.id === id);
}

export function verifyPassword(user: any, password: string) {
  return bcrypt.compareSync(password, user.password_hash);
}

export function activateLicense(userId: string, paymentMethod: string, amount: number, currency: string) {
  const db = loadDB();
  const user = db.users.find((u: any) => u.id === userId);
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

// ── Session Operations ─────────────────────────────────────
export function createSession(userId: string, token: string, expiresAt: string) {
  const db = loadDB();
  db.sessions.push({ token, user_id: userId, expires_at: expiresAt });
  saveDB(db);
}

export function getSession(token: string) {
  const db = loadDB();
  return db.sessions.find((s: any) => s.token === token && new Date(s.expires_at) > new Date());
}

export function deleteSession(token: string) {
  const db = loadDB();
  db.sessions = db.sessions.filter((s: any) => s.token !== token);
  saveDB(db);
}

// ── Update Operations ──────────────────────────────────────
export function createUpdate(version: string, title: string, description: string, downloadUrl: string, checksum: string) {
  const db = loadDB();
  const id = uuidv4();
  db.updates.push({
    id, version, title, description, download_url: downloadUrl, checksum,
    release_date: new Date().toISOString(), is_active: 0, sent_emails: 0,
  });
  saveDB(db);
  return id;
}

export function getActiveUpdates() {
  const db = loadDB();
  return db.updates.filter((u: any) => u.is_active === 1).sort((a: any, b: any) =>
    new Date(b.release_date).getTime() - new Date(a.release_date).getTime()
  );
}

export function getAllUpdates() {
  const db = loadDB();
  return db.updates.sort((a: any, b: any) =>
    new Date(b.release_date).getTime() - new Date(a.release_date).getTime()
  );
}

export function activateUpdate(id: string) {
  const db = loadDB();
  const update = db.updates.find((u: any) => u.id === id);
  if (update) {
    update.is_active = 1;
    saveDB(db);
  }
}

export function markUpdateSent(id: string) {
  const db = loadDB();
  const update = db.updates.find((u: any) => u.id === id);
  if (update) {
    update.sent_emails = (update.sent_emails || 0) + 1;
    saveDB(db);
  }
}

// ── User Updates ───────────────────────────────────────────
export function getUserUpdates(userId: string) {
  const db = loadDB();
  return getActiveUpdates().map((u: any) => ({
    ...u,
    downloaded: 0,
    downloaded_at: null,
  }));
}

export function markUpdateDownloaded(userId: string, updateId: string) {
  // Track in user_updates if needed later
}

// ── Audit ──────────────────────────────────────────────────
export function logAudit(action: string, userId?: string, ip?: string, details?: string) {
  const db = loadDB();
  db.auditLog.push({
    id: Date.now(), action, user_id: userId || null, ip_address: ip || null,
    details: details || null, created_at: new Date().toISOString(),
  });
  saveDB(db);
}

// ── Stats ──────────────────────────────────────────────────
export function getStats() {
  const db = loadDB();
  return {
    totalUsers: db.users.length,
    paidUsers: db.users.filter((u: any) => u.is_paid === 1).length,
    totalUpdates: db.updates.length,
  };
}

// Reset for testing
export function resetDB() {
  saveDB({ users: [], updates: [], sessions: [], auditLog: [] });
}
