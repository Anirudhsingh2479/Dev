export function otpTemplate(otp) {
  return `<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>AI Dev Team OTP</title>
  </head>
  <body style="margin:0;padding:0;background:#101318;color:#e7ebf0;font-family:Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#101318;padding:28px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#171c23;border:1px solid #2b333f;border-radius:10px;overflow:hidden;">
            <tr>
              <td style="padding:28px;background:#14231f;border-bottom:1px solid rgba(123,220,181,.18);">
                <p style="margin:0 0 8px;color:#7bdcb5;font-size:12px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">AI Dev Team</p>
                <h1 style="margin:0;color:#ffffff;font-size:28px;">Verify your dashboard login</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px;">
                <p style="margin:0 0 18px;color:#c7d0dc;line-height:1.6;">Use this one-time password to finish creating your AI Dev dashboard account.</p>
                <div style="margin:22px 0;padding:18px;text-align:center;background:#101318;border:1px solid rgba(123,220,181,.25);border-radius:8px;">
                  <strong style="font-size:34px;letter-spacing:8px;color:#7bdcb5;">${otp}</strong>
                </div>
                <p style="margin:0;color:#8d98a7;line-height:1.6;">This OTP expires in 5 minutes. If you did not request this, you can ignore this email.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>`;
}

export function registrationTemplate(name) {
  return `<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Welcome to AI Dev Team</title>
  </head>
  <body style="margin:0;padding:0;background:#101318;color:#e7ebf0;font-family:Arial,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#101318;padding:28px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#171c23;border:1px solid #2b333f;border-radius:10px;overflow:hidden;">
            <tr>
              <td style="padding:28px;background:#14231f;border-bottom:1px solid rgba(123,220,181,.18);">
                <p style="margin:0 0 8px;color:#7bdcb5;font-size:12px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">AI Dev Team</p>
                <h1 style="margin:0;color:#ffffff;font-size:28px;">Account created</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px;">
                <p style="margin:0 0 14px;color:#c7d0dc;line-height:1.6;">Hi ${name},</p>
                <p style="margin:0;color:#c7d0dc;line-height:1.6;">Your dashboard account is ready. You can now create projects, monitor runs, and manage generated app previews.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>`;
}
