// src/lib/email.ts
// Email service using Resend (free tier: 3,000 emails/month)
// Replace with actual API key in production

const RESEND_API_KEY = process.env.RESEND_API_KEY || '';
const FROM_EMAIL = 'updates@localmind.ai';

export async function sendUpdateEmail(userEmail: string, userName: string, version: string, title: string) {
  if (!RESEND_API_KEY) {
    console.log(`[EMAIL MOCK] To: ${userEmail} | Subject: LocalMind ${version} Update Available`);
    return { success: true, mock: true };
  }
  
  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: FROM_EMAIL,
        to: userEmail,
        subject: `LocalMind ${version} Update Available!`,
        html: `
          <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>LocalMind Update: ${version}</h2>
            <p>Hi ${userName || 'there'},</p>
            <p>A new update is available for your LocalMind AI:</p>
            <h3>${title}</h3>
            <p><a href="https://portal.localmind.ai/login" 
               style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
               Log in to Download
            </a></p>
            <p>Your license key gives you lifetime free updates.</p>
          </div>
        `,
      }),
    });
    
    return await response.json();
  } catch (e) {
    console.error('Email send failed:', e);
    return { success: false, error: e };
  }
}

export async function sendWelcomeEmail(userEmail: string, licenseKey: string) {
  if (!RESEND_API_KEY) {
    console.log(`[EMAIL MOCK] To: ${userEmail} | Subject: Welcome to LocalMind!`);
    return { success: true, mock: true };
  }
  
  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${RESEND_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: FROM_EMAIL,
        to: userEmail,
        subject: 'Welcome to LocalMind — Your License Key',
        html: `
          <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome to LocalMind!</h2>
            <p>Your purchase is complete. Here are your details:</p>
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
              <strong>License Key:</strong> <code>${licenseKey}</code>
            </div>
            <p><a href="https://portal.localmind.ai/login" 
               style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
               Log in to Download
            </a></p>
          </div>
        `,
      }),
    });
    
    return await response.json();
  } catch (e) {
    console.error('Email send failed:', e);
    return { success: false, error: e };
  }
}
