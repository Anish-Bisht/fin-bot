"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/threads";
import { ScrollArea } from "@/components/ui/scroll-area";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import { TrendingUp } from "lucide-react";

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

export default function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <ScrollArea className="flex-1">
      <div className="min-h-full flex flex-col">
        {messages.length === 0 && !isLoading ? (
          <div className="flex-1 flex items-center justify-center py-12">
            <div className="text-center space-y-4 max-w-md px-6">
              <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <TrendingUp className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight">FinBot</h2>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Your AI-powered equity research analyst. Ask about any stock ticker
                to get a structured analyst brief with fundamentals, valuation
                signals, and market sentiment.
              </p>
              <div className="flex flex-wrap gap-2 justify-center pt-2">
                {["Analyze AAPL", "Brief on TSLA", "Research MSFT"].map((q) => (
                  <span
                    key={q}
                    className="text-xs px-3 py-1.5 rounded-full bg-muted text-muted-foreground border border-border"
                  >
                    {q}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto p-4 space-y-1 w-full">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={bottomRef} className="h-4" />
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
