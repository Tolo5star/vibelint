// bad_vibes.ts — A TypeScript file that triggers all 8 VibeLint rules.
// This is what "vibe-coded" production code actually looks like.

import express from "express";
import cors from "cors";
import { Logger } from "./logger";       // <-- unused import (AI-QUAL-003)
import { Validator } from "./validator"; // <-- unused import (AI-QUAL-003)

// AI-SEC-001: Hardcoded secret disguised as placeholder
const OPENAI_API_KEY = "sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx";
const STRIPE_KEY = "sk_live_51ABC123DEF456GHI789JKL";

// AI-SEC-004: Over-permissive CORS
const app = express();
app.use(cors({ origin: '*' }));

// AI-QUAL-001: any type when specific type is inferrable
async function fetchUsers(): Promise<any> {
  const response: any = await fetch("/api/users");
  const data: any = await response.json();
  return data;
}

// AI-LOGIC-001: Async function in .map()
async function processItems(items: string[]) {
  const results = items.map(async (item) => {
    const res = await fetch(`/api/process/${item}`);
    return res.json();
  });
  // results is Promise[]  not the resolved values!
  return results;
}

// AI-LOGIC-002: Catch-all error handling (empty catch)
async function riskyOperation() {
  try {
    await fetch("/api/dangerous");
  } catch (e) {
  }
}

// AI-LOGIC-002: Catch with only console.log
async function anotherRiskyOp() {
  try {
    await fetch("/api/also-dangerous");
  } catch (err) {
    console.log(err);
  }
}

// AI-SEC-002: XSS via innerHTML
function renderComment(comment: string) {
  const el = document.getElementById("comments");
  el.innerHTML = comment;  // unsanitized user input!
}

// AI-LOGIC-004: Missing null check after .find()
function getUserName(users: { id: number; name: string }[], targetId: number) {
  const user = users.find(u => u.id === targetId);
  return user.name;  // user might be undefined!
}

// AI-SEC-002: XSS via dangerouslySetInnerHTML (JSX-style, but in .ts for demo)
// (Would be caught in .tsx files with JSX parsing)

// More AI-QUAL-001: as any assertion
function processData(input: unknown) {
  const data = input as any;
  return data.foo.bar.baz;
}
