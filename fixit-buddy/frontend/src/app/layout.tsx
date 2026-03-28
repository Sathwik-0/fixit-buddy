import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FixIt Buddy — EU Right-to-Repair Navigator",
  description: "AI-powered repair assistant for electronics",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
