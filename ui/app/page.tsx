"use client";

import { useState, useEffect, useCallback } from "react";
import { TooltipProvider } from "@/components/ui/tooltip";
import ThreadSidebar from "@/components/sidebar/ThreadSidebar";
import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import { sendMessage, getUserMe, logout } from "@/lib/api";
import { getThreads, createThread, getThread, appendMessage, deleteThread, Thread, Message } from "@/lib/threads";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function Home() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  // Load threads on mount and create one if none exist
  useEffect(() => {
    getUserMe().then(usr => {
      setUser(usr);
    }).catch(() => {
      router.push("/login");
    });

    const loadedThreads = getThreads();
    if (loadedThreads.length === 0) {
      // Create first thread automatically
      const newThread = createThread();
      setThreads([newThread]);
      setActiveThreadId(newThread.id);
    } else {
      setThreads(loadedThreads);
      if (!activeThreadId) {
        setActiveThreadId(loadedThreads[0].id);
      }
    }
    // Only run on mount or when router changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  const activeThread = activeThreadId ? threads.find(t => t.id === activeThreadId) : undefined;
  const messages = activeThread?.messages || [];

  const handleNewThread = useCallback(() => {
    const newThread = createThread();
    setThreads(getThreads());
    setActiveThreadId(newThread.id);
  }, []);

  const handleSelectThread = useCallback((id: string) => {
    setActiveThreadId(id);
  }, []);

  const handleDeleteThread = useCallback((id: string) => {
    deleteThread(id);
    const remaining = getThreads();
    setThreads(remaining);
    if (activeThreadId === id) {
      if (remaining.length > 0) {
        setActiveThreadId(remaining[0].id);
      } else {
        setActiveThreadId(null);
      }
    }
  }, [activeThreadId]);

  const handleSendMessage = useCallback(
    async (query: string) => {
      if (!activeThreadId) return;

      // Add user message
      appendMessage(activeThreadId, "user", query);
      setThreads(getThreads());

      setIsLoading(true);
      try{
        const response = await sendMessage(query, activeThreadId);
        appendMessage(activeThreadId, "assistant", response.result, {
          route: response.route,
          warnings: response.warnings,
          sources: response.sources,
          executionTime: response.execution_time,
          agentThoughts: response.agent_thoughts
        });
        setThreads(getThreads());
      } catch (err) {
        console.error("Failed to get response:", err);
        const errorMessage = err instanceof Error ? err.message : "An error occurred while processing your request.";
        appendMessage(activeThreadId, "assistant", `Error: ${errorMessage}`);
        setThreads(getThreads());
      } finally {
        setIsLoading(false);
      }
    },
    [activeThreadId]
  );

  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden bg-background">
        {/* Sidebar */}
        <div className="hidden md:flex md:w-64 border-r border-border flex-col justify-between">
          <ThreadSidebar
            threads={threads}
            activeThreadId={activeThreadId}
            onSelectThread={handleSelectThread}
            onNewThread={handleNewThread}
            onDeleteThread={handleDeleteThread}
          />
          <div className="p-4 border-t space-y-2">
            <div className="text-sm font-semibold mb-2 text-zinc-600 dark:text-zinc-300">
              {user?.username} ({user?.role})
            </div>
            {user?.role === "c_level" && (
              <Button className="w-full text-xs" variant="outline" onClick={() => router.push("/admin")}>
                Admin Dashboard
              </Button>
            )}
            <Button className="w-full text-xs" variant="destructive" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-h-0">
          <ChatWindow messages={messages} isLoading={isLoading} />
          <ChatInput onSend={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </TooltipProvider>
  );
}
