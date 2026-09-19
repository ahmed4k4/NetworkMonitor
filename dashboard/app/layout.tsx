"use client";

import "./globals.css";

import { usePathname } from "next/navigation";

import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { ToastProvider } from "@/components/ui/toast";

const routeTitles: Record<string, string> = {
  "/": "Overview",
  "/devices": "Devices",
  "/devices/[id]": "Device Details",
  "/traffic": "Live Traffic",
  "/flows": "Network Flows",
  "/domains": "Domains",
  "/applications": "Applications",
  "/protocols": "Protocols",
  "/analytics": "Analytics",
  "/history": "History",
  "/alerts": "Alerts",
  "/reports": "Reports",
  "/rules": "Rules",
  "/limits": "Bandwidth Limits",
  "/firewall": "Firewall",
  "/quotas": "Quotas",
  "/interfaces": "Interfaces",
  "/system": "System",
  "/settings": "Settings",
  "/data-management": "Data Management",
  "/login": "Sign In",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  // Find matching route title
  const routeTitle = Object.entries(routeTitles).find(([route]) => {
    if (route === "/") return pathname === "/";
    if (route.includes("[id]")) {
      const pattern = route.replace("[id]", "[^/]+");
      return new RegExp(`^${pattern}$`).test(pathname);
    }
    return pathname.startsWith(route);
  })?.[1];

  const pageTitle = routeTitle ? `${routeTitle} | Network Control Center` : "Network Control Center";

  return (
    <html lang="en">
      <head>
        <title>{pageTitle}</title>
        <meta name="description" content="Network Control Center - Network Intelligence Platform" />
        <link rel="icon" href="/favicon.svg" sizes="any" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.svg" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#3B82F6" />
      </head>
      <body className="min-h-screen bg-background text-foreground">
        <ToastProvider>
          {!isLoginPage && <Sidebar />}

          <div className={isLoginPage ? "" : "lg:pl-64"}>
            {!isLoginPage && <Header />}

            <main className={isLoginPage ? "" : "p-4 sm:p-6 lg:p-8"} id="main-content" tabIndex={-1}>
              {children}
            </main>
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}
