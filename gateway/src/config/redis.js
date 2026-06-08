import { createClient } from "redis";

const redisUrl = process.env.REDIS_URL || "redis://redis:6379/0";

export const redisClient = createClient({ url: redisUrl });

redisClient.on("error", (error) => {
  console.warn("Gateway Redis unavailable:", error.message);
});

export async function connectRedis() {
  if (redisClient.isOpen) return;

  try {
    await redisClient.connect();
    console.log("Gateway connected to Redis");
  } catch (error) {
    console.warn("Gateway Redis connection skipped:", error.message);
  }
}
