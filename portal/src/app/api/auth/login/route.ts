// src/app/api/auth/login/route.ts
import { NextResponse } from 'next/server';
import { getUserByEmail, verifyPassword, createSession } from '@/lib/db';
import { generateToken } from '@/lib/auth';

export async function POST(req: Request) {
  try {
    const { email, password } = await req.json();
    const user = getUserByEmail(email);
    
    if (!user || !verifyPassword(user, password)) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }
    
    const token = generateToken(user.id);
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    createSession(user.id, token, expiresAt);
    
    const response = NextResponse.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        licenseKey: user.license_key,
        isPaid: user.is_paid === 1,
      }
    });
    
    response.cookies.set('token', token, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60,
    });
    
    return response;
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
