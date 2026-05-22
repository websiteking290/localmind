# LocalMind Customer Portal

Authentication, payments, update delivery system for LocalMind USB product.

## Deploy Options

### Option 1: Railway (Recommended)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```
- Free tier: $5 credit/month
- Persistent SQLite via volume
- Auto-SSL
- Custom domain support

### Option 2: VPS (DigitalOcean, Hetzner, etc)
```bash
# Clone repo
git clone https://github.com/websiteking290/localmind.git
cd localmind/portal

# Run with Docker
docker-compose up -d
```

### Option 3: Vercel (Limited)
- Static pages work
- API routes need external database (Supabase/Neon)
- SQLite won't persist

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes | Random string for JWT signing |
| `STRIPE_SECRET_KEY` | For card payments | Stripe API key |
| `COINBASE_API_KEY` | For crypto | Coinbase Commerce key |
| `RESEND_API_KEY` | For emails | Resend API key |

## Features

- **Auth:** JWT sessions, bcrypt password hashing
- **Payments:** Stripe (cards) + Coinbase Commerce (crypto)
- **Admin:** Create updates, activate, notify all paid users
- **Email:** Welcome + update notifications via Resend
- **License keys:** Auto-generated on purchase

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/api/auth/register` | POST | Create account |
| `/api/auth/login` | POST | Log in |
| `/api/auth/logout` | POST | Log out |
| `/api/user` | GET | Get user + available updates |
| `/api/checkout` | POST | Process payment |
| `/api/admin/updates` | GET/POST | List / create updates |
| `/api/admin/activate` | POST | Activate an update |
| `/api/admin/notify` | POST | Email all paid users |
| `/api/admin/stats` | GET | Dashboard stats |

## Local Development

```bash
cd portal
npm install
npm run dev
# Visit http://localhost:3000
```

## Database

SQLite auto-creates on first run:
- `users` - accounts, license keys, payment status
- `updates` - version info, download URLs
- `user_updates` - download tracking
- `sessions` - JWT token storage
- `audit_log` - security logging

## License

MIT
