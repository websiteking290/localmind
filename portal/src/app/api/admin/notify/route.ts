// src/app/api/admin/notify/route.ts
import { NextResponse } from 'next/server';
import { getAllUpdates, getStats } from '@/lib/db';
import { sendUpdateEmail } from '@/lib/email';

export async function POST(req: Request) {
  try {
    const { updateId } = await req.json();
    
    // Demo mode - log instead of sending
    const stats = getStats();
    console.log(`[EMAIL] Would notify ${stats.paidUsers} paid users about update ${updateId}`);
    
    return NextResponse.json({
      success: true,
      message: `Update notification queued for ${stats.paidUsers} paid users (demo mode)`,
      stats,
    });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
