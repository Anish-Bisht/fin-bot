"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      router.push("/");
    } catch (err: any) {
      setError("Invalid username or password");
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-zinc-950 text-white">
      <div className="w-full max-w-sm p-8 bg-zinc-900 rounded-lg shadow-xl border border-white/10">
        <h1 className="text-2xl font-semibold mb-6 text-center tracking-tight">Login to FinBot</h1>
        {error && <div className="text-red-400 mb-4 text-sm text-center">{error}</div>}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-zinc-400">Username</label>
            <input
              className="w-full p-2 rounded bg-zinc-800 border border-zinc-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1 text-zinc-400">Password</label>
            <input
              type="password"
              className="w-full p-2 rounded bg-zinc-800 border border-zinc-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white">
            Login
          </Button>
        </form>
      </div>
    </div>
  );
}
