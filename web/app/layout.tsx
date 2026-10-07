import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ru-ya",
  description: "Scholarly dream interpretation with citations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
