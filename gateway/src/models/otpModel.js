import mongoose from "mongoose";

const otpSchema = new mongoose.Schema({
  emailId: {
    type: String,
    required: true,
    trim: true,
    lowercase: true,
  },
  otp: {
    type: String,
    required: true,
  },
  createdAt: {
    type: Date,
    default: Date.now,
    expires: 5 * 60,
  },
});

export default mongoose.model("DashboardOTP", otpSchema);
