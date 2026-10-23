import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "MASDS - Multi-Agent Software Development System",
  description:
    "Autonomous multi-agent orchestration for end-to-end software delivery. From requirement to deployed container.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-[#0a0a0f] text-gray-100 antialiased selection:bg-brand-500/30 selection:text-brand-200`}>
        <div className="relative min-h-screen flex flex-col bg-grid-pattern">
          {children}
        </div>
      </body>
    </html>
  );
}
