"use client";

import { Thread } from "@/lib/threads";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Plus, MessageSquare, Trash2, TrendingUp } from "lucide-react";

interface ThreadSidebarProps {
  threads: Thread[];
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
  onNewThread: () => void;
  onDeleteThread: (id: string) => void;
}

export default function ThreadSidebar({
  threads,
  activeThreadId,
  onSelectThread,
  onNewThread,
  onDeleteThread,
}: ThreadSidebarProps) {
  return (
    <div className="flex flex-col h-full bg-card/50 border-r border-border">
      {/* Header */}
      <div className="p-4 flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-emerald-500 flex items-center justify-center">
          <TrendingUp className="h-4 w-4 text-white" />
        </div>
        <span className="font-semibold text-sm tracking-tight">FinBot</span>
      </div>

      <div className="px-3">
        <Button
          onClick={onNewThread}
          variant="outline"
          className="w-full justify-start gap-2 rounded-xl text-sm h-10 border-dashed"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <Separator className="my-3" />

      {/* Thread List */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1 pb-4">
          {threads.length === 0 && (
            <p className="text-xs text-muted-foreground text-center py-6">
              No conversations yet
            </p>
          )}
          {threads.map((thread) => (
            <div key={thread.id} className="group relative">
              <button
                onClick={() => onSelectThread(thread.id)}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-colors flex items-center gap-2 ${
                  activeThreadId === thread.id
                    ? "bg-accent text-accent-foreground"
                    : "hover:bg-muted/50 text-muted-foreground"
                }`}
              >
                <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-60" />
                <span className="truncate flex-1">{thread.title}</span>
              </button>

              <div
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteThread(thread.id);
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-destructive/10 hover:text-destructive cursor-pointer"
                title="Delete thread"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
