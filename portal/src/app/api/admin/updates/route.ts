// src/app/api/admin/updates/route.ts
import { NextResponse } from 'next/server';
import { getAllUpdates, createUpdate, activateUpdate } from '@/lib/db';

export async function GET() {
  try {
    const updates = getAllUpdates();
    return NextResponse.json({ updates });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const { version, title, description, downloadUrl, checksum } = await req.json();
    
    if (!version || !title || !downloadUrl) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
    }
    
    const id = createUpdate(version, title, description, downloadUrl, checksum);
    return NextResponse.json({ success: true, id });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
