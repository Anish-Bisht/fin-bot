"use client";

import { useEffect, useRef } from "react";
import { Message } from "@/lib/threads";
import { ScrollArea } from "@/components/ui/scroll-area";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";
import { ShieldCheck } from "lucide-react";

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  userRole?: string;
  onSuggestionClick?: (query: string) => void;
}

// Role-specific welcome content
const ROLE_WELCOME: Record<string, { label: string; description: string; suggestions: string[] }> = {
  engineering: {
    label: "Engineering",
    description:
      "Ask about system architecture, incident reports, sprint metrics, SLA reports, and engineering documentation.",
    suggestions: [
      "What is the system architecture?",
      "Show me the latest sprint metrics",
      "What is the SLA for our services?",
    ],
  },
  finance: {
    label: "Finance",
    description:
      "Access quarterly financial reports, department budgets, vendor payment summaries, and financial metrics.",
    suggestions: [
      "What is the Q3 revenue summary?",
      "Show department budget breakdown",
      "What are the vendor payments?",
    ],
  },
  marketing: {
    label: "Marketing",
    description:
      "Review campaign performance, customer acquisition reports, and marketing analytics across all quarters.",
    suggestions: [
      "How did the Q4 marketing campaign perform?",
      "What is the customer acquisition cost?",
      "Show marketing report for 2024",
    ],
  },
  c_level: {
    label: "Executive",
    description:
      "Full access to all departments — engineering, finance, marketing, and HR. Ask about any area of the business.",
    suggestions: [
      "What is the overall company strategy?",
      "Show me the quarterly financial report",
      "What are the sprint metrics?",
    ],
  },
  employee: {
    label: "General",
    description:
      "Access company-wide resources like the employee handbook, HR policies, leave information, and general guidelines.",
    suggestions: [
      "What is the leave policy?",
      "Tell me about company benefits",
      "What is the code of conduct?",
    ],
  },
};

const DEFAULT_WELCOME = ROLE_WELCOME.employee;

export default function ChatWindow({ messages, isLoading, userRole, onSuggestionClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const welcome = ROLE_WELCOME[userRole?.toLowerCase() || ""] || DEFAULT_WELCOME;

  return (
    <ScrollArea className="flex-1">
      <div className="min-h-full flex flex-col">
        {messages.length === 0 && !isLoading ? (
          <div className="flex-1 flex items-center justify-center py-12">
            <div className="text-center space-y-4 max-w-md px-6">
              <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <ShieldCheck className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-2xl font-semibold tracking-tight">
                Welcome, {welcome.label}
              </h2>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {welcome.description}
              </p>
              <div className="flex flex-wrap gap-2 justify-center pt-2">
                {welcome.suggestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => onSuggestionClick?.(q)}
                    className="text-xs px-3 py-1.5 rounded-full bg-muted text-muted-foreground border border-border hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
                  >
                    {q}
                  </button>
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
