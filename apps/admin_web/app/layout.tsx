import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata = { title: "Anime Platform Admin", description: "Working admin panel" };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="ru"><body>{children}</body></html>; }
