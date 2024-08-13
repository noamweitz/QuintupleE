import type { Metadata } from "next";
import { Inter, Karla } from "next/font/google";
import "./globals.css";
import NavBar from '../components/NavBar/NavBar';

const inter = Inter({ subsets: ["latin"] });
// const karla = Karla({subsets: ["latin"]});

export const metadata: Metadata = {
  title: "Quintuple E",
  description: "Dashboard for the system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} text-secondary`}>
        <header className="w-full text-primary"><NavBar></NavBar></header>
          {children}
      </body>
    </html>
  );
}
