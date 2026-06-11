"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Navbar from "@/components/Navbar";
import WelcomeScreen from "@/components/WelcomeScreen";
import ChatBubble from "@/components/ChatBubble";
import TypingIndicator from "@/components/TypingIndicator";
import InputBar from "@/components/InputBar";
import ErrorToast from "@/components/ErrorToast";
import { sendQuery } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function HomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorVisible, setErrorVisible] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inFlightRef = useRef(false);

  const hasStarted = messages.length > 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const runQuery = useCallback(async (query: string) => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    setLoading(true);

    const userMessage: ChatMessage = { id: newId(), role: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await sendQuery(query);
      const assistantMessage: ChatMessage = {
        id: newId(),
        role: "assistant",
        text: response.answer,
        response,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setErrorVisible(true);
      setTimeout(() => setErrorVisible(false), 4000);
    } finally {
      setLoading(false);
      inFlightRef.current = false;
    }
  }, []);

  return (
    <div className="flex min-h-screen flex-col overflow-hidden">
      <Navbar />

      <main className="w-full flex-grow overflow-y-auto pb-52 pt-28 sm:pb-48 sm:pt-32">
        <div className="mx-auto max-w-[1000px] px-4 sm:px-6">
          {!hasStarted && !loading && <WelcomeScreen onSelectQuestion={runQuery} />}

          {hasStarted && (
            <div className="space-y-6">
              {messages.map((msg) => (
                <ChatBubble key={msg.id} role={msg.role} text={msg.text} response={msg.response} />
              ))}
              {loading && <TypingIndicator />}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </main>

      <InputBar onSubmit={runQuery} disabled={loading} />
      <ErrorToast visible={errorVisible} />
    </div>
  );
}
