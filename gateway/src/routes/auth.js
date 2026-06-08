import { Router } from "express";
import bcrypt from "bcryptjs";
import crypto from "crypto";
import jwt from "jsonwebtoken";
import validator from "validator";
import User from "../models/userModel.js";
import OTP from "../models/otpModel.js";
import { redisClient } from "../config/redis.js";
import { sendMail } from "../config/mail.js";
import { publicUser, requireAuth } from "../middleware/auth.js";
import { saveUser } from "../services/projectStore.js";
import { otpTemplate, registrationTemplate } from "../templates/emailTemplates.js";

const router = Router();
const cookieOptions = {
  httpOnly: true,
  sameSite: "lax",
  maxAge: 24 * 60 * 60 * 1000,
};

function signToken(user) {
  return jwt.sign(
    { emailId: user.emailId, userName: user.userName, role: "user" },
    process.env.JWT_SECRET_KEY,
    { expiresIn: 60 * 60 },
  );
}

function isStrongPassword(password) {
  return validator.isStrongPassword(password || "", {
    minLength: 8,
    minLowercase: 1,
    minUppercase: 1,
    minNumbers: 1,
    minSymbols: 1,
  });
}

async function generateUniqueOtp() {
  let otp = crypto.randomInt(100000, 999999).toString();
  while (await OTP.findOne({ otp })) {
    otp = crypto.randomInt(100000, 999999).toString();
  }
  return otp;
}

async function persistProjectUser(user) {
  const reply = publicUser(user);
  await saveUser({
    user_id: reply.user_id,
    email: reply.email,
    display_name: reply.display_name,
  });
  return reply;
}

router.post("/sendotp", async (req, res, next) => {
  try {
    const { emailId, userName } = req.body || {};
    if (!emailId || !userName) {
      res.status(400).json({ success: false, message: "Email and username are required" });
      return;
    }

    const existingEmail = await User.findOne({ emailId });
    if (existingEmail) {
      res.status(401).json({ success: false, message: "User already registered" });
      return;
    }

    const existingUserName = await User.findOne({ userName });
    if (existingUserName) {
      res.status(401).json({ success: false, message: "UserName already taken" });
      return;
    }

    const otp = await generateUniqueOtp();
    await OTP.create({ emailId, otp });
    await sendMail(emailId, "Your AI Dev Team OTP", otpTemplate(otp));
    res.json({ success: true, message: "Otp Sent Succesfully" });
  } catch (error) {
    next(error);
  }
});

router.post("/register", async (req, res, next) => {
  try {
    const { firstName, lastName, userName, emailId, password, otp, profilePhoto } = req.body || {};
    if (!firstName || !lastName || !userName || !emailId || !password || !otp) {
      res.status(403).json({ success: false, message: "All fields are required." });
      return;
    }
    if (!isStrongPassword(password)) {
      res.status(400).json({
        success: false,
        message: "Password must include uppercase, lowercase, number, and symbol.",
      });
      return;
    }

    const recentOtp = await OTP.findOne({ emailId }).sort({ createdAt: -1 });
    if (!recentOtp) {
      res.status(400).json({ success: false, message: "OTP Not Found." });
      return;
    }
    if (String(otp) !== recentOtp.otp) {
      res.status(400).json({ success: false, message: "Invalid OTP." });
      return;
    }

    const existingUser = await User.findOne({ $or: [{ emailId }, { userName }] });
    if (existingUser?.userName === userName) {
      res.status(409).json({ success: false, message: "UserName already taken" });
      return;
    }
    if (existingUser?.emailId === String(emailId).toLowerCase()) {
      res.status(409).json({ success: false, message: "User already registered" });
      return;
    }

    const user = await User.create({
      firstName,
      lastName,
      userName,
      emailId,
      password: await bcrypt.hash(password, 10),
      profilePhoto,
      role: "user",
    });
    await OTP.deleteMany({ emailId });

    const token = signToken(user);
    sendMail(user.emailId, "Welcome to AI Dev Team", registrationTemplate(user.firstName)).catch((error) => {
      console.warn("Welcome email failed:", error.message);
    });
    const reply = await persistProjectUser(user);
    res.cookie("token", token, cookieOptions);
    res.status(201).json({
      user: reply,
      message: "User Registered Successfully",
    });
  } catch (error) {
    next(error);
  }
});

router.post("/login", async (req, res, next) => {
  try {
    const { emailId, userName, password } = req.body || {};
    if (!(emailId || userName) || !password) {
      res.status(400).json({ success: false, message: "Username/Email and Password are required." });
      return;
    }

    const user = await User.findOne({ $or: [{ emailId }, { userName }] });
    if (!user || !(await bcrypt.compare(password, user.password))) {
      res.status(401).json({ success: false, message: "Invalid Credentials" });
      return;
    }

    const token = signToken(user);
    const reply = await persistProjectUser(user);
    res.cookie("token", token, cookieOptions);
    res.json({ user: reply, message: "LogIn Successful !" });
  } catch (error) {
    next(error);
  }
});

router.post("/logout", async (req, res, next) => {
  try {
    const { token } = req.cookies;
    if (!token) {
      res.status(200).send("Already logged out.");
      return;
    }

    try {
      const payload = jwt.verify(token, process.env.JWT_SECRET_KEY);
      if (redisClient.isOpen) {
        await redisClient.set(`token:${token}`, "blocked");
        await redisClient.expireAt(`token:${token}`, payload.exp);
      }
    } catch {
      res.clearCookie("token", cookieOptions);
      res.status(200).send("Invalid token, logged out.");
      return;
    }

    res.clearCookie("token", cookieOptions);
    res.status(200).send("User logged out succesfully!");
  } catch (error) {
    next(error);
  }
});

router.get("/check", requireAuth, async (req, res) => {
  res.json({ user: req.user, message: "Valid User!" });
});

export default router;
