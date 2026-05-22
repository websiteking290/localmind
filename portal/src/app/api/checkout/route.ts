// src/app/api/checkout/route.ts
import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { activateLicense, getUserById } from '@/lib/db';

// NOTE: Replace with actual Stripe + Coinbase API keys
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY || '';
const COINBASE_API_KEY = process.env.COINBASE_API_KEY || '';

export async function POST(req: Request) {
  try {
    const user = await getCurrentUser();
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
    }
    
    const { method, amount = 129, currency = 'USD' } = await req.json();
    // method: 'stripe' | 'crypto'
    
    if (method === 'stripe') {
      // In production: Create Stripe Checkout Session
      // const session = await stripe.checkout.sessions.create({...})
      // Return { url: session.url }
      
      // Demo mode: simulate payment
      activateLicense(user.id, 'stripe', amount, currency);
      
      return NextResponse.json({
        success: true,
        message: 'Payment processed (demo mode)',
        licenseKey: user.license_key,
        downloadUrl: 'https://localmind.ai/download',
      });
    }
    
    if (method === 'crypto') {
      // In production: Create Coinbase Commerce Charge
      // const charge = await coinbase.charges.create({...})
      // Return { url: charge.hosted_url }
      
      // Demo mode: simulate payment
      activateLicense(user.id, 'crypto', amount, currency);
      
      return NextResponse.json({
        success: true,
        message: 'Crypto payment processed (demo mode)',
        licenseKey: user.license_key,
        downloadUrl: 'https://localmind.ai/download',
      });
    }
    
    return NextResponse.json({ error: 'Invalid payment method' }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
