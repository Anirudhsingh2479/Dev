import fs from "fs/promises";
import path from "path";

const EXCLUDED_NAMES = new Set([
  ".git",
  "node_modules",
  "dist",
  "build",
  ".vite",
  ".cache",
  "coverage",
]);

const EXCLUDED_FILES = new Set([
  ".env",
  ".DS_Store",
]);

const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let index = 0; index < 256; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) {
      value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table[index] = value >>> 0;
  }
  return table;
})();

function getSandboxRoot() {
  return path.resolve(process.env.SANDBOX_ROOT || path.join(process.cwd(), "..", "sandbox"));
}

function isSafeSandboxId(sandboxId) {
  return /^sandbox-\d+$/.test(String(sandboxId || ""));
}

function shouldSkip(entryName) {
  return EXCLUDED_NAMES.has(entryName) || EXCLUDED_FILES.has(entryName) || entryName.endsWith(".log");
}

function crc32(buffer) {
  let value = 0xffffffff;
  for (const byte of buffer) {
    value = crcTable[(value ^ byte) & 0xff] ^ (value >>> 8);
  }
  return (value ^ 0xffffffff) >>> 0;
}

function dosDateTime(date) {
  const year = Math.max(date.getFullYear(), 1980);
  const dosTime = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
  const dosDate = ((year - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate();
  return { dosTime, dosDate };
}

function localHeader(nameBuffer, fileBuffer, stat) {
  const header = Buffer.alloc(30);
  const checksum = crc32(fileBuffer);
  const { dosTime, dosDate } = dosDateTime(stat.mtime);

  header.writeUInt32LE(0x04034b50, 0);
  header.writeUInt16LE(20, 4);
  header.writeUInt16LE(0x0800, 6);
  header.writeUInt16LE(0, 8);
  header.writeUInt16LE(dosTime, 10);
  header.writeUInt16LE(dosDate, 12);
  header.writeUInt32LE(checksum, 14);
  header.writeUInt32LE(fileBuffer.length, 18);
  header.writeUInt32LE(fileBuffer.length, 22);
  header.writeUInt16LE(nameBuffer.length, 26);
  header.writeUInt16LE(0, 28);

  return { header, checksum, dosTime, dosDate };
}

function centralHeader(nameBuffer, fileBuffer, meta, offset) {
  const header = Buffer.alloc(46);
  header.writeUInt32LE(0x02014b50, 0);
  header.writeUInt16LE(20, 4);
  header.writeUInt16LE(20, 6);
  header.writeUInt16LE(0x0800, 8);
  header.writeUInt16LE(0, 10);
  header.writeUInt16LE(meta.dosTime, 12);
  header.writeUInt16LE(meta.dosDate, 14);
  header.writeUInt32LE(meta.checksum, 16);
  header.writeUInt32LE(fileBuffer.length, 20);
  header.writeUInt32LE(fileBuffer.length, 24);
  header.writeUInt16LE(nameBuffer.length, 28);
  header.writeUInt16LE(0, 30);
  header.writeUInt16LE(0, 32);
  header.writeUInt16LE(0, 34);
  header.writeUInt16LE(0, 36);
  header.writeUInt32LE(0, 38);
  header.writeUInt32LE(offset, 42);
  return header;
}

function endRecord(fileCount, centralSize, centralOffset) {
  const record = Buffer.alloc(22);
  record.writeUInt32LE(0x06054b50, 0);
  record.writeUInt16LE(0, 4);
  record.writeUInt16LE(0, 6);
  record.writeUInt16LE(fileCount, 8);
  record.writeUInt16LE(fileCount, 10);
  record.writeUInt32LE(centralSize, 12);
  record.writeUInt32LE(centralOffset, 16);
  record.writeUInt16LE(0, 20);
  return record;
}

async function walkFiles(root, dir = root) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    if (shouldSkip(entry.name)) continue;

    const absolutePath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...await walkFiles(root, absolutePath));
    } else if (entry.isFile()) {
      const relativePath = path.relative(root, absolutePath).split(path.sep).join("/");
      files.push({ absolutePath, relativePath });
    }
  }

  return files;
}

export async function createProjectZipBuffer(sandboxId) {
  if (!isSafeSandboxId(sandboxId)) {
    const error = new Error("invalid sandbox id");
    error.statusCode = 400;
    throw error;
  }

  const sandboxRoot = getSandboxRoot();
  const sandboxPath = path.resolve(sandboxRoot, sandboxId);
  if (!sandboxPath.startsWith(`${sandboxRoot}${path.sep}`)) {
    const error = new Error("invalid sandbox path");
    error.statusCode = 400;
    throw error;
  }

  let rootStat;
  try {
    rootStat = await fs.stat(sandboxPath);
  } catch {
    const error = new Error("sandbox folder not found");
    error.statusCode = 404;
    throw error;
  }
  if (!rootStat.isDirectory()) {
    const error = new Error("sandbox path is not a folder");
    error.statusCode = 400;
    throw error;
  }

  const files = await walkFiles(sandboxPath);
  if (!files.length) {
    const error = new Error("sandbox has no downloadable files");
    error.statusCode = 400;
    throw error;
  }

  const localParts = [];
  const centralParts = [];
  let offset = 0;

  for (const file of files) {
    const fileBuffer = await fs.readFile(file.absolutePath);
    const stat = await fs.stat(file.absolutePath);
    const zipName = `${sandboxId}/${file.relativePath}`;
    const nameBuffer = Buffer.from(zipName, "utf8");
    const meta = localHeader(nameBuffer, fileBuffer, stat);
    const localPart = Buffer.concat([meta.header, nameBuffer, fileBuffer]);

    localParts.push(localPart);
    centralParts.push(Buffer.concat([centralHeader(nameBuffer, fileBuffer, meta, offset), nameBuffer]));
    offset += localPart.length;
  }

  const centralDirectory = Buffer.concat(centralParts);
  return Buffer.concat([
    ...localParts,
    centralDirectory,
    endRecord(files.length, centralDirectory.length, offset),
  ]);
}
