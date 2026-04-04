"use client";

import { Message } from "@/lib/threads";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { User, Bot, AlertTriangle, Route, FileText, Clock, BrainCircuit } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} mb-4`}>
      <Avatar className="h-8 w-8 shrink-0 mt-0.5">
        <AvatarFallback
          className={
            isUser
              ? "bg-indigo-600 text-white"
              : "bg-emerald-600 text-white"
          }
        >
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-indigo-600 text-white rounded-br-md"
            : "bg-card border border-border rounded-bl-md"
        }`}
      >
        {isUser ? (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-sm dark:prose-invert prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-headings:my-2 prose-pre:my-2 prose-pre:bg-zinc-900 prose-pre:border prose-pre:border-border prose-code:text-emerald-400 prose-strong:text-foreground max-w-none text-sm leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
              {message.content}
            </ReactMarkdown>

            {/* Guardrail Warning Banner */}
            {message.warnings && (
              <div className="mt-4 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-500 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                <div className="text-sm font-medium">
                  {message.warnings}
                </div>
              </div>
            )}

            {/* Semantic Route & Latency */}
            {(message.route && message.route !== "unclassified" || message.executionTime) && (
              <div className="mt-3 flex flex-wrap items-center gap-3">
                {message.route && message.route !== "unclassified" && (
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground bg-zinc-800/50 w-fit px-2 py-0.5 rounded border border-border">
                    <Route className="h-3 w-3" />
                    <span>{message.route.replace("_route", "")}</span>
                  </div>
                )}
                {message.executionTime && (
                  <div className="flex items-center gap-1 text-[10px] text-zinc-500">
                    <Clock className="h-2.5 w-2.5" />
                    <span>{message.executionTime}s</span>
                  </div>
                )}
              </div>
            )}

            {/* Agent Thoughts (Collapsible/Subtle) */}
            {message.agentThoughts && (
              <div className="mt-3 p-2 rounded bg-zinc-900/50 border border-zinc-800 text-[11px] text-zinc-400 italic font-mono space-y-1">
                <div className="flex items-center gap-1 opacity-70 mb-1 not-italic font-sans uppercase tracking-wider text-[9px]">
                  <BrainCircuit className="h-2.5 w-2.5" />
                  Agent Process
                </div>
                {message.agentThoughts}
              </div>
            )}

            {/* Sources / Citations */}
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 space-y-1">
                <div className="text-xs font-semibold text-zinc-400 flex items-center gap-1.5">
                  <FileText className="h-3 w-3" />
                  Sources Cited
                </div>
                <div className="flex flex-wrap gap-2">
                  {message.sources.map((src, i) => (
                    <span key={i} className="text-[11px] px-2 py-1 rounded bg-zinc-800 border border-zinc-700 text-zinc-300">
                      {src}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
