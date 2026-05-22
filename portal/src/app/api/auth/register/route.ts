// src/app/api/auth/register/route.ts
import { NextResponse } from 'next/server';
import { createUser, getUserByEmail } from '@/lib/db';

export async function POST(req: Request) {
  try {
    const { email, password, name } = await req.json();
    
    if (!email || !password || password.length < 8) {
      return NextResponse.json({ error: 'Invalid email or password (min 8 chars)' }, { status: 400 });
    }
    
    const existing = getUserByEmail(email);
    if (existing) {
      return NextResponse.json({ error: 'Email already registered' }, { status: 409 });
    }
    
    const user = createUser(email, password, name);
    
    return NextResponse.json({ 
      success: true, 
      user: { id: user.id, email: user.email, licenseKey: user.licenseKey }
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
