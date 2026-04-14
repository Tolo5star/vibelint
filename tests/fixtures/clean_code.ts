// clean_code.ts — A well-written TypeScript file that triggers NO rules.

import express from "express";
import cors from "cors";

const app = express();

// Proper CORS config with specific origins
app.use(cors({ origin: ["https://myapp.com", "https://staging.myapp.com"] }));

// API key from environment
const apiKey = process.env.OPENAI_API_KEY;

// Proper typing
interface User {
  id: number;
  name: string;
  email: string;
}

async function fetchUsers(): Promise<User[]> {
  const response = await fetch("/api/users");
  const data: User[] = await response.json();
  return data;
}

// Correct async pattern with Promise.all
async function processItems(items: string[]): Promise<unknown[]> {
  const results = await Promise.all(
    items.map(async (item) => {
      const res = await fetch(`/api/process/${item}`);
      return res.json();
    })
  );
  return results;
}

// Proper error handling
async function riskyOperation(): Promise<void> {
  try {
    await fetch("/api/dangerous");
  } catch (error) {
    console.error("Operation failed:", error);
    throw new Error(`Failed to complete operation: ${error}`);
  }
}

// Safe HTML rendering
function renderComment(comment: string): void {
  const el = document.getElementById("comments");
  if (el) {
    el.textContent = comment; // textContent is safe
  }
}

// Proper null check after .find()
function getUserName(users: User[], targetId: number): string | undefined {
  const user = users.find((u) => u.id === targetId);
  return user?.name;
}
