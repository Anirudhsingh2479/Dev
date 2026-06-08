import jwt from "jsonwebtoken";
import User from "../models/userModel.js";
import { redisClient } from "../config/redis.js";

export function publicUser(user) {
  return {
    user_id: String(user._id),
    email: user.emailId,
    display_name: `${user.firstName}${user.lastName ? ` ${user.lastName}` : ""}`,
    firstName: user.firstName,
    lastName: user.lastName,
    userName: user.userName,
    emailId: user.emailId,
    role: "user",
    profilePhoto: user.profilePhoto || "",
  };
}

export async function requireAuth(req, res, next) {
  try {
    const { token } = req.cookies;
    if (!token) {
      res.status(401).json({ error: "Unauthenticated" });
      return;
    }

    const payload = jwt.verify(token, process.env.JWT_SECRET_KEY);
    if (!payload?.emailId || !payload?.userName) {
      res.status(401).json({ error: "Invalid token" });
      return;
    }

    if (redisClient.isOpen) {
      const isBlocked = await redisClient.exists(`token:${token}`);
      if (isBlocked) {
        res.status(401).json({ error: "Invalid token" });
        return;
      }
    }

    const user = await User.findOne({
      $or: [{ emailId: payload.emailId }, { userName: payload.userName }],
    });
    if (!user) {
      res.status(401).json({ error: "User does not exist" });
      return;
    }

    req.user = publicUser(user);
    req.authUser = user;
    next();
  } catch (error) {
    res.status(401).json({ error: error.message || "Unauthenticated" });
  }
}
