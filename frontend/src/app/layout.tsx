import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "VerifyAI — AI-Powered Fake News Verification",
  description:
    "Detect misinformation instantly. Paste a headline, upload a screenshot, or enter a URL — and get an AI-powered truth verdict in seconds.",
  keywords: [
    "fake news",
    "fact check",
    "misinformation",
    "AI verification",
    "screenshot analysis",
  ],
};

import { NewsTicker } from "@/components/news-ticker";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <NewsTicker />
        {children}
      </body>
    </html>
  );
}
