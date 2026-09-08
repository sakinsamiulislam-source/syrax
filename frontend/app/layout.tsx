import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SYRAX — AI Trading & Portfolio Agent | Binance Agent OS",
  description: "Research. Reason. Risk. Execute. Autonomous AI Agent built on Binance Agent OS.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090D16] text-slate-100 min-h-screen antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
        {children}
      </body>
    </html>
  );
}
