import mongoose from "mongoose";

export async function connectMongo() {
  if (!process.env.MONGO_URI) {
    throw new Error("MONGO_URI is required for dashboard auth");
  }

  if (mongoose.connection.readyState === 1) return;
  await mongoose.connect(process.env.MONGO_URI);
  console.log("Gateway connected to MongoDB");
}
