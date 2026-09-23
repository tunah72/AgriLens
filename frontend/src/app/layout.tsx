import type { Metadata } from "next";
import { Inter, Playfair_Display, Be_Vietnam_Pro } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "../lib/i18n";

const inter = Inter({
  subsets: ["latin", "vietnamese"],
  variable: "--font-inter",
  display: "swap",
});

const playfair = Playfair_Display({
  subsets: ["latin", "vietnamese"],
  variable: "--font-playfair",
  display: "swap",
});

const beVietnamPro = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-bevietnam",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AgriLens - Hệ thống chẩn đoán bệnh lá lúa & cà phê",
  description: "AgriLens - Ứng dụng trí tuệ nhân tạo chẩn đoán bệnh cây trồng và khuyến nghị điều trị cho nông dân Việt Nam.",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" className="h-full">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                if (typeof window !== 'undefined') {
                  var origDefine = Object.defineProperty;
                  Object.defineProperty = function(obj, prop, descriptor) {
                    if ((obj === window || obj === globalThis) && prop === 'ethereum') {
                      try {
                        return origDefine.call(Object, obj, prop, Object.assign({}, descriptor, { configurable: true }));
                      } catch {
                        try {
                          if (descriptor && 'value' in descriptor) {
                            obj.ethereum = descriptor.value;
                          }
                        } catch {}
                        return obj;
                      }
                    }
                    return origDefine.apply(Object, arguments);
                  };

                  window.addEventListener('error', function(event) {
                    if (event && event.message && event.message.indexOf('ethereum') !== -1) {
                      event.stopImmediatePropagation();
                      event.preventDefault();
                      return true;
                    }
                  }, true);

                  window.addEventListener('unhandledrejection', function(event) {
                    if (event && event.reason && String(event.reason).indexOf('ethereum') !== -1) {
                      event.stopImmediatePropagation();
                      event.preventDefault();
                    }
                  }, true);
                }
              } catch {}

              try {
                if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              } catch {}
            `,
          }}
        />
      </head>
      <body className={`${inter.variable} ${playfair.variable} ${beVietnamPro.variable} font-sans h-full bg-background text-foreground antialiased selection:bg-claude-orange/30 selection:text-claude-orange`}>
        <LanguageProvider defaultLang="vi">
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
