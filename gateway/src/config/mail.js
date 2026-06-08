import nodemailer from "nodemailer";

function readMailConfig() {
  return {
    host: process.env.MAIL_HOST,
    port: Number(process.env.MAIL_PORT || 587),
    secure: String(process.env.MAIL_SECURE || "false").toLowerCase() === "true",
    user: process.env.MAIL_USER,
    pass: process.env.MAIL_PASS,
  };
}

export function mailConfigured() {
  const config = readMailConfig();
  return Boolean(config.host && config.port && config.user && config.pass);
}

export async function sendMail(to, subject, html) {
  const config = readMailConfig();
  if (!mailConfigured()) {
    throw new Error("Mail is not configured. Set MAIL_HOST, MAIL_PORT, MAIL_SECURE, MAIL_USER, and MAIL_PASS.");
  }

  const transporter = nodemailer.createTransport({
    host: config.host,
    port: config.port,
    secure: config.secure,
    auth: {
      user: config.user,
      pass: config.pass,
    },
  });

  return transporter.sendMail({
    from: `"AI Dev Team" <${config.user}>`,
    to,
    subject,
    text: "Your email client does not support HTML. Please enable HTML view.",
    html,
  });
}
