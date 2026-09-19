"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Bell, Search, Menu, Sun, Moon, User, LogOut, ChevronDown, Settings, Wifi, WifiOff, X, LayoutDashboard, Cpu, Activity, GitBranch, Globe, AppWindow, AlertTriangle, SlidersHorizontal } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { StatusIndicator } from "@/components/design-system";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useToast } from "@/components/ui/toast";

export default function Header() {
  const router = useRouter();
  const { addToast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");
  const [systemOnline, setSystemOnline] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchFocused, setSearchFocused] = useState(false);
  
  const userMenuButtonRef = useRef<HTMLButtonElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  
  // WebSocket status
  const wsStatus = useWebSocket(() => {});

  const checkSystemStatus = useCallback(async () => {
    try {
      const health = await api.getHealth();
      setSystemOnline(health.status === "ok");
    } catch {
      setSystemOnline(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(checkSystemStatus, 0);
    const interval = setInterval(checkSystemStatus, 30000);
    return () => {
      clearTimeout(timeoutId);
      clearInterval(interval);
    };
  }, [checkSystemStatus]);

  // Initialize dark mode from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = savedTheme ? savedTheme === "dark" : prefersDark;
    // Use setTimeout to avoid synchronous state update warning
    const timeoutId = setTimeout(() => {
      setDarkMode(isDark);
      if (isDark) {
        document.documentElement.classList.add("dark");
      }
    }, 0);
    return () => clearTimeout(timeoutId);
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    if (newDarkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
      addToast("Dark mode enabled", { variant: "info" as const });
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
      addToast("Light mode enabled", { variant: "info" as const });
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      router.push(`/traffic?search=${encodeURIComponent(searchTerm.trim())}`);
      addToast(`Searching for "${searchTerm.trim()}"`, { variant: "default" as const });
    }
  };

  const handleLogout = () => {
    api.logout();
    router.push("/login");
    addToast("Logged out successfully", { variant: "success" as const });
  };

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node) &&
          userMenuButtonRef.current && !userMenuButtonRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Handle keyboard navigation for user menu
  const handleUserMenuKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case "Escape":
        setUserMenuOpen(false);
        userMenuButtonRef.current?.focus();
        break;
      case "ArrowDown":
        e.preventDefault();
        userMenuRef.current?.querySelector("button")?.focus();
        break;
      case "Tab":
        if (e.shiftKey) {
          // Shift+Tab from first item should close menu
          const firstItem = userMenuRef.current?.querySelector("button") as HTMLElement;
          if (document.activeElement === firstItem) {
            e.preventDefault();
            setUserMenuOpen(false);
            userMenuButtonRef.current?.focus();
          }
        }
        break;
      default:
        break;
    }
  }, []);

  const handleSearchKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setSearchFocused(false);
      searchInputRef.current?.blur();
      setSearchTerm("");
    }
  }, []);

  return (
    <header className={cn(
      "sticky top-0 z-30 flex h-16 items-center justify-between border-b",
      "bg-background/90 backdrop-blur-sm px-4 sm:px-6",
      "transition-all duration-200"
    )}>
      {/* Mobile Menu Toggle */}
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="lg:hidden p-2 rounded-lg hover:bg-hover transition-colors"
        aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={mobileMenuOpen}
        aria-controls="mobile-menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Search */}
      <form onSubmit={handleSearch} className="relative hidden md:block flex-1 max-w-md mx-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" aria-hidden="true" />
        <input
          ref={searchInputRef}
          type="search"
          placeholder="Search devices, traffic, domains... (⌘K)"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => setSearchFocused(true)}
          onBlur={() => setSearchFocused(false)}
          onKeyDown={handleSearchKeyDown}
          className={cn(
            "w-full h-9 pl-9 pr-3 text-sm bg-surface border border-border",
            "rounded-lg placeholder:text-text-muted",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
            "transition-all duration-200",
            searchFocused && "ring-2 ring-primary-500 border-transparent max-w-lg"
          )}
          aria-label="Global search"
          aria-expanded="false"
        />
      </form>

      {/* Right Section */}
      <div className="flex items-center gap-3">
        {/* System Status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface/50 border border-border transition-all duration-200">
          <StatusIndicator variant={systemOnline ? "online" : "offline"} size="sm" pulse={systemOnline} />
          <span className="text-body-sm text-text-secondary font-medium">
            {systemOnline ? "System Online" : "System Offline"}
          </span>
        </div>

        {/* WebSocket Status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface/50 border border-border transition-all duration-200">
          <StatusIndicator 
            variant={wsStatus === "open" ? "online" : wsStatus === "connecting" ? "warning" : "offline"} 
            size="sm" 
            pulse={wsStatus === "open"} 
          />
          <span className="text-body-sm text-text-secondary font-medium">
            {wsStatus === "open" ? "Live" : wsStatus === "connecting" ? "Connecting..." : "Offline"}
          </span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleDarkMode}
          className={cn(
            "p-2 rounded-lg transition-all duration-150",
            "hover:bg-hover text-text-secondary",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-background",
            "active:scale-95"
          )}
          aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          aria-pressed={darkMode}
        >
          {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        {/* Alerts */}
        <button
          onClick={() => router.push("/alerts")}
          className={cn(
            "relative p-2 rounded-lg transition-all duration-150",
            "hover:bg-hover text-text-secondary",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-background",
            "active:scale-95"
          )}
          aria-label="View alerts"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-danger-500" aria-hidden="true" />
        </button>

        {/* User Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            ref={userMenuButtonRef}
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            onKeyDown={handleUserMenuKeyDown}
            className={cn(
              "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-150",
              "hover:bg-hover text-text-secondary",
              "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-background",
              "active:scale-95"
            )}
            aria-expanded={userMenuOpen}
            aria-haspopup="true"
            aria-controls="user-menu"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400">
              <User className="h-4 w-4" />
            </div>
            <span className="hidden sm:block text-sm font-medium text-text-primary">Admin</span>
            <ChevronDown className={cn("h-4 w-4 text-text-muted transition-transform duration-150", userMenuOpen && "rotate-180")} aria-hidden="true" />
          </button>

          {userMenuOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setUserMenuOpen(false)}
                aria-hidden="true"
              />
              <div 
                id="user-menu"
                className="absolute right-0 mt-2 w-48 rounded-lg border border-border bg-surface-elevated shadow-lg py-1 z-50"
                role="menu"
                onKeyDown={handleUserMenuKeyDown}
              >
                <div className="px-3 py-2 border-b border-border">
                  <p className="text-sm font-medium text-text-primary">Admin</p>
                  <p className="text-xs text-text-muted">admin@network.local</p>
                </div>
                <button
                  onClick={() => { router.push("/settings"); setUserMenuOpen(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text-secondary hover:bg-hover hover:text-text-primary transition-colors"
                  role="menuitem"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </button>
                <hr className="my-1 border-border" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-danger-600 hover:bg-danger-50 dark:hover:bg-danger-900/30 transition-colors"
                  role="menuitem"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      {mobileMenuOpen && (
        <div
          id="mobile-menu"
          ref={mobileMenuRef}
          className="lg:hidden fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex flex-col"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile navigation"
        >
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">Navigation</h2>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-2 rounded-lg hover:bg-hover transition-colors"
              aria-label="Close navigation menu"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <nav className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              <Link href="/" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <LayoutDashboard className="h-5 w-5" />
                <span>Overview</span>
              </Link>
              <Link href="/devices" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <Cpu className="h-5 w-5" />
                <span>Devices</span>
              </Link>
              <Link href="/traffic" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <Activity className="h-5 w-5" />
                <span>Live Traffic</span>
              </Link>
              <Link href="/flows" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <GitBranch className="h-5 w-5" />
                <span>Network Flows</span>
              </Link>
              <Link href="/domains" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <Globe className="h-5 w-5" />
                <span>Domains</span>
              </Link>
              <Link href="/applications" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <AppWindow className="h-5 w-5" />
                <span>Applications</span>
              </Link>
              <Link href="/analytics" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <LayoutDashboard className="h-5 w-5" />
                <span>Analytics</span>
              </Link>
              <Link href="/alerts" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <AlertTriangle className="h-5 w-5" />
                <span>Alerts</span>
              </Link>
              <Link href="/rules" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <SlidersHorizontal className="h-5 w-5" />
                <span>Rules</span>
              </Link>
              <Link href="/settings" className="flex items-center gap-3 px-3 py-2 rounded-lg text-text-secondary hover:bg-hover hover:text-text-primary transition-colors">
                <Settings className="h-5 w-5" />
                <span>Settings</span>
              </Link>
            </div>
          </nav>
          <div className="border-t p-4">
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors text-text-secondary hover:bg-danger-50 hover:text-danger-600 dark:hover:bg-danger-900/30"
            >
              <LogOut className="h-4 w-4 text-danger-500" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}