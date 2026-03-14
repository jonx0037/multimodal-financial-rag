import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Image from "next/image";
import ThemeToggle from "@/components/ThemeToggle";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FinRAG",
  description: "Cross-modal semantic search over financial documents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <header className="flex items-center justify-between border-b border-card-border px-6 py-3">
          <div className="flex items-center gap-2">
            <Image
              src="/images/finrag-logo.png"
              alt="FinRAG"
              width={28}
              height={28}
              className="rounded-sm"
            />
            <span className="font-mono text-sm font-semibold tracking-tight">
              finrag.io
            </span>
          </div>
          <ThemeToggle />
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
