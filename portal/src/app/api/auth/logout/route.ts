// src/app/api/auth/logout/route.ts
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { deleteSession } from '@/lib/db';

export async function POST() {
  const cookieStore = cookies();
  const token = cookieStore.get('token')?.value;
  
  if (token) {
    deleteSession(token);
  }
  
  const response = NextResponse.json({ success: true });
  response.cookies.set('token', '', { maxAge: 0 });
  
  return response;
}
