import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { deDE } from "@clerk/localizations";
import { Inter, Newsreader } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Mika — Lernbegleiter",
  description: "Ein ruhiger Lernbegleiter für Mathe und Deutsch, Klasse 2 bis 4.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className={`${inter.variable} ${newsreader.variable} h-full`}>
      <body className="min-h-full font-sans">
        {/* The parent signs in, but they are signing into a German product. */}
        <ClerkProvider localization={deDE} afterSignOutUrl="/">
          {children}
        </ClerkProvider>
      </body>
    </html>
  );
}
