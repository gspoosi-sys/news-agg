import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Balanced News",
  description: "Stay informed without the overwhelm",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#f8f7f4] text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
