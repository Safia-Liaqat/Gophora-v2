import React from "react";
import ChatAgent from "../components/ChatAgent/ChatAgent";


export default function TestChat() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-[#120024] via-[#1a0033] to-[#2b0054]">
      {/* The chat component will float here */}
      <ChatAgent/>
    </div>
  );
}
