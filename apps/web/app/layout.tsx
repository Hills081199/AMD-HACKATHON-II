import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
  weight: ["500", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Atlas — Mastery Tree",
  description: "Turn any pile of documents into an optimal, playable learning path.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-background text-on-surface font-sans antialiased">{children}</body>
    </html>
  );
}
