export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  route?: string;
  warnings?: string;
  sources?: string[];
  executionTime?: number;
  agentThoughts?: string;
  timestamp: number;
}

export interface Thread {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

const STORAGE_KEY_PREFIX = "finbot-threads";
const CURRENT_USER_KEY = "finbot-current-user";

function getStorageKey(): string {
  if (typeof window === "undefined") return STORAGE_KEY_PREFIX;
  const username = localStorage.getItem(CURRENT_USER_KEY) || "anonymous";
  return `${STORAGE_KEY_PREFIX}-${username}`;
}

/** Call this after login to scope thread storage to the current user. */
export function setCurrentUser(username: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem(CURRENT_USER_KEY, username);
  }
}

/** Call this on logout to clear the current user scope. */
export function clearCurrentUser() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(CURRENT_USER_KEY);
  }
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function getThreads(): Thread[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(getStorageKey());
  if (!raw) return [];
  try {
    return JSON.parse(raw) as Thread[];
  } catch {
    return [];
  }
}

function saveThreads(threads: Thread[]) {
  localStorage.setItem(getStorageKey(), JSON.stringify(threads));
}

export function createThread(): Thread {
  const thread: Thread = {
    id: generateId(),
    title: "New Chat",
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
  const threads = getThreads();
  threads.unshift(thread);
  saveThreads(threads);
  return thread;
}

export function getThread(id: string): Thread | undefined {
  return getThreads().find((t) => t.id === id);
}

export function appendMessage(
  threadId: string,
  role: "user" | "assistant",
  content: string,
  extra?: { route?: string; warnings?: string; sources?: string[]; executionTime?: number; agentThoughts?: string }
): Message {
  const threads = getThreads();
  const thread = threads.find((t) => t.id === threadId);
  if (!thread) throw new Error("Thread not found");

  const message: Message = {
    id: generateId(),
    role,
    content,
    route: extra?.route,
    warnings: extra?.warnings,
    sources: extra?.sources,
    executionTime: extra?.executionTime,
    agentThoughts: extra?.agentThoughts,
    timestamp: Date.now(),
  };

  thread.messages.push(message);
  thread.updatedAt = Date.now();

  // Auto-title from first user message
  if (role === "user" && thread.messages.filter((m) => m.role === "user").length === 1) {
    thread.title = content.length > 40 ? content.substring(0, 40) + "…" : content;
  }

  saveThreads(threads);
  return message;
}

export function deleteThread(id: string) {
  const threads = getThreads().filter((t) => t.id !== id);
  saveThreads(threads);
}
