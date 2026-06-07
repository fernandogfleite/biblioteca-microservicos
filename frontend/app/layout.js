import "./globals.css";
import { IBM_Plex_Sans, Sora } from "next/font/google";

const headingFont = Sora({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["500", "600", "700"],
});

const bodyFont = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600"],
});

export const metadata = {
  title: "Biblioteca Online - Painel Next.js",
  description: "Frontend modular em Next.js para catalogo, emprestimos e recomendacoes",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body className={`${headingFont.variable} ${bodyFont.variable}`}>{children}</body>
    </html>
  );
}