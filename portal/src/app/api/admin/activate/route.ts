// src/app/api/admin/activate/route.ts
import { NextResponse } from 'next/server';
import { activateUpdate } from '@/lib/db';

export async function POST(req: Request) {
  try {
    const { id } = await req.json();
    activateUpdate(id);
    return NextResponse.json({ success: true });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
