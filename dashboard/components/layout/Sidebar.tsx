"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useRef, useEffect, useCallback } from "react";
import {
  LayoutDashboard,
  Monitor,
  Activity,
  GitBranch,
  Globe,
  AppWindow,
  Settings,
  Database,
  AlertTriangle,
  FileText,
  Shield,
  SlidersHorizontal,
  HardDrive,
  Cpu,
  Wifi,
  LogOut,
  ChevronRight,
  ChevronDown,
  Search,
  Archive,
  Keyboard,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { StatusIndicator } from "@/components/design-system";

const navGroups = [
  {
    label: "Monitoring",
    icon: Monitor,
    items: [
      { name: "Overview", href: "/", icon: LayoutDashboard },
      { name: "Devices", href: "/devices", icon: Cpu },
      { name: "Traffic", href: "/traffic", icon: Activity },
      { name: "Flows", href: "/flows", icon: GitBranch },
      { name: "Domains", href: "/domains", icon: Globe },
      { name: "Applications", href: "/applications", icon: AppWindow },
      { name: "Protocols", href: "/protocols", icon: Database },
    ],
  },
  {
    label: "Analysis",
    icon: AlertTriangle,
    items: [
      { name: "Analytics", href: "/analytics", icon: LayoutDashboard },
      { name: "History", href: "/history", icon: FileText },
      { name: "Alerts", href: "/alerts", icon: AlertTriangle },
      { name: "Reports", href: "/reports", icon: FileText },
    ],
  },
  {
    label: "Control",
    icon: Shield,
    items: [
      { name: "Rules", href: "/rules", icon: SlidersHorizontal },
      { name: "Limits", href: "/limits", icon: Shield },
      { name: "Firewall", href: "/firewall", icon: Shield },
      { name: "Quotas", href: "/quotas", icon: Database },
    ],
  },
  {
    label: "System",
    icon: Settings,
    items: [
      { name: "Interfaces", href: "/interfaces", icon: Wifi },
      { name: "System", href: "/system", icon: HardDrive },
      { name: "Settings", href: "/settings", icon: Settings },
    ],
  },
  {
    label: "Data Management",
    icon: Archive,
    items: [
      { name: "Data Center", href: "/data-management", icon: Archive },
    ],
  },
];

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavGroup {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  items: NavItem[];
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set(["Analysis", "Control", "System", "Data Management"]));
  const [systemOnline, setSystemOnline] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{ group: string; item: NavItem }[]>([]);
  const [searchFocused, setSearchFocused] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  
  const searchInputRef = useRef<HTMLInputElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const groupButtonsRef = useRef<Map<string, HTMLButtonElement>>(new Map());
  const navLinksRef = useRef<HTMLAnchorElement[]>([]);

  const checkSystemStatus = useCallback(async () => {
    try {
      const health = await api.getHealth();
      setSystemOnline(health.status === "ok");
    } catch {
      setSystemOnline(false);
    }
  }, []);

  const handleLogout = () => {
    api.logout();
    router.push("/login");
  };

  const toggleGroup = useCallback((label: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }
      return next;
    });
  }, []);

  const isGroupCollapsed = (label: string) => collapsedGroups.has(label);

  const isItemActive = (item: NavItem) => {
    return pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
  };

  const isGroupActive = (group: NavGroup) => {
    return group.items.some(isItemActive);
  };

  // Keyboard navigation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const allItems = navGroups.flatMap((g) => g.items);
    const visibleItems = allItems.filter(item => {
      if (searchQuery) {
        return item.name.toLowerCase().includes(searchQuery.toLowerCase());
      }
      return true;
    });

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (searchFocused) {
          setFocusedIndex((prev) => Math.min(prev + 1, searchResults.length - 1));
        }
        break;
      case "ArrowUp":
        e.preventDefault();
        if (searchFocused) {
          setFocusedIndex((prev) => Math.max(prev - 1, -1));
        }
        break;
      case "Enter":
        if (searchFocused && focusedIndex >= 0 && searchResults[focusedIndex]) {
          e.preventDefault();
          router.push(searchResults[focusedIndex].item.href);
          setSearchQuery("");
          setSearchResults([]);
          setFocusedIndex(-1);
          searchInputRef.current?.blur();
        }
        break;
      case "Escape":
        if (searchFocused) {
          setSearchQuery("");
          setSearchResults([]);
          setFocusedIndex(-1);
          searchInputRef.current?.blur();
        }
        break;
      case "Home":
        if (!searchFocused) {
          e.preventDefault();
          const firstLink = sidebarRef.current?.querySelector('nav a[href]') as HTMLElement;
          firstLink?.focus();
        }
        break;
      case "End":
        if (!searchFocused) {
          e.preventDefault();
          const links = sidebarRef.current?.querySelectorAll('nav a[href]') as NodeListOf<HTMLElement>;
          links[links.length - 1]?.focus();
        }
        break;
      case "Tab":
        // Allow natural tab behavior but track focus
        break;
      default:
        break;
    }
  }, [router, searchQuery, searchFocused, focusedIndex, searchResults]);

  // Search functionality
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    setFocusedIndex(-1);
    
    if (query.trim()) {
      const results: { group: string; item: NavItem }[] = [];
      navGroups.forEach((group) => {
        group.items.forEach((item) => {
          if (item.name.toLowerCase().includes(query.toLowerCase())) {
            results.push({ group: group.label, item });
          }
        });
      });
      setSearchResults(results);
    } else {
      setSearchResults([]);
    }
  }, []);

  const handleSearchFocus = useCallback(() => {
    setSearchFocused(true);
  }, []);

  const handleSearchBlur = useCallback(() => {
    // Delay to allow click on results
    setTimeout(() => {
      setSearchFocused(false);
      setFocusedIndex(-1);
    }, 200);
  }, []);

  const handleResultClick = (href: string) => {
    router.push(href);
    setSearchQuery("");
    setSearchResults([]);
    setFocusedIndex(-1);
    searchInputRef.current?.blur();
  };

  // Register group buttons for keyboard navigation
  const registerGroupButton = useCallback((label: string, element: HTMLButtonElement | null) => {
    if (element) {
      groupButtonsRef.current.set(label, element);
    } else {
      groupButtonsRef.current.delete(label);
    }
  }, []);

  // Focus management for group toggles
  const handleGroupKeyDown = useCallback((e: React.KeyboardEvent, label: string) => {
    const groups = navGroups.map(g => g.label);
    const currentIndex = groups.indexOf(label);
    
    switch (e.key) {
      case "ArrowRight":
        e.preventDefault();
        if (isGroupCollapsed(label)) {
          toggleGroup(label);
        } else {
          // Move to first item in group
          const firstItem = sidebarRef.current?.querySelector(`#nav-group-${label} a`) as HTMLElement;
          firstItem?.focus();
        }
        break;
      case "ArrowLeft":
        e.preventDefault();
        if (!isGroupCollapsed(label)) {
          toggleGroup(label);
        }
        break;
      case "ArrowDown":
        e.preventDefault();
        const nextGroup = groups[(currentIndex + 1) % groups.length];
        groupButtonsRef.current.get(nextGroup)?.focus();
        break;
      case "ArrowUp":
        e.preventDefault();
        const prevGroup = groups[(currentIndex - 1 + groups.length) % groups.length];
        groupButtonsRef.current.get(prevGroup)?.focus();
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        toggleGroup(label);
        break;
      default:
        break;
    }
  }, [isGroupCollapsed, toggleGroup]);

  // Initialize
  useEffect(() => {
    const interval = setInterval(checkSystemStatus, 30000);
    // Initial check - use setTimeout to avoid synchronous state update warning
    const timeoutId = setTimeout(checkSystemStatus, 0);
    return () => {
      clearInterval(interval);
      clearTimeout(timeoutId);
    };
  }, [checkSystemStatus]);

  // Update focused index when search results change
  const prevSearchResultsLength = useRef(searchResults.length);
  useEffect(() => {
    if (searchResults.length > 0 && searchResults.length !== prevSearchResultsLength.current && focusedIndex === -1) {
      setFocusedIndex(0);
    }
    prevSearchResultsLength.current = searchResults.length;
  }, [searchResults.length, focusedIndex]);

  return (
    <aside 
      ref={sidebarRef}
      className="fixed left-0 top-0 z-40 h-screen w-64 border-r bg-surface flex flex-col transition-all duration-300 lg:w-64"
      onKeyDown={handleKeyDown}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Brand Header */}
      <div className="border-b p-4 bg-surface/50 backdrop-blur-sm">
        <Link href="/" className="flex items-center gap-3" aria-label="Network Control Center Home">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-500">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="text-card-title truncate text-text-primary">Network Control</h1>
            <p className="text-caption text-text-muted">Network Intelligence Platform</p>
          </div>
        </Link>
      </div>

      {/* System Status */}
      <div className="border-b p-4 bg-surface/30">
        <div className="flex items-center gap-3">
          <StatusIndicator variant={systemOnline ? "online" : "offline"} size="md" pulse={systemOnline} />
          <span className="text-body-sm text-text-secondary flex-1 truncate">
            {systemOnline ? "System Online" : "System Offline"}
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3" aria-label="Main navigation">
        {/* Search */}
        <div className="mb-3 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" aria-hidden="true" />
          <input
            ref={searchInputRef}
            type="search"
            placeholder="Search pages... (⌘K)"
            value={searchQuery}
            onChange={handleSearchChange}
            onFocus={handleSearchFocus}
            onBlur={handleSearchBlur}
            className={cn(
              "w-full pl-9 pr-3 py-2 text-sm bg-background border border-border rounded-lg placeholder:text-text-muted",
              "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
              "transition-all duration-200",
              searchFocused && "ring-2 ring-primary-500 border-transparent"
            )}
            aria-label="Search navigation pages"
            aria-expanded={searchResults.length > 0}
            aria-controls="search-results"
            aria-activedescendant={focusedIndex >= 0 ? `search-result-${focusedIndex}` : undefined}
          />
          {searchResults.length > 0 && searchFocused && (
            <ul 
              id="search-results"
              className="absolute top-full left-0 right-0 mt-1 max-h-60 overflow-y-auto bg-surface-elevated border border-border rounded-lg shadow-lg z-10"
              role="listbox"
            >
              {searchResults.map((result, index) => (
                <li key={`${result.group}-${result.item.name}`} role="option">
                  <button
                    id={`search-result-${index}`}
                    onClick={() => handleResultClick(result.item.href)}
                    className={cn(
                      "w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors",
                      index === focusedIndex
                        ? "bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300"
                        : "text-text-secondary hover:bg-hover hover:text-text-primary"
                    )}
                    role="option"
                    aria-selected={index === focusedIndex}
                  >
                    <result.item.icon className="h-4 w-4 flex-shrink-0 text-text-muted" />
                    <span className="flex-1 truncate font-medium">{result.item.name}</span>
                    <span className="text-xs text-text-muted uppercase tracking-wider">{result.group}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {navGroups.map((group) => (
          <div key={group.label} className="mb-2">
            <button
              ref={(el) => registerGroupButton(group.label, el)}
              type="button"
              onClick={() => toggleGroup(group.label)}
              onKeyDown={(e) => handleGroupKeyDown(e, group.label)}
              className={cn(
                "w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-text-muted hover:text-text-primary transition-colors rounded-lg",
                "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-surface",
                isGroupActive(group) && "text-primary-500",
                isGroupCollapsed(group.label) && "text-text-muted"
              )}
              aria-expanded={!isGroupCollapsed(group.label)}
              aria-controls={`nav-group-${group.label}`}
              aria-pressed={!isGroupCollapsed(group.label)}
            >
              <group.icon className={cn("h-4 w-4 flex-shrink-0", isGroupActive(group) && "text-primary-500")} />
              <span className="flex-1 text-left truncate">{group.label}</span>
              <ChevronDown
                className={cn(
                  "h-4 w-4 flex-shrink-0 text-text-muted transition-transform duration-200",
                  !isGroupCollapsed(group.label) && "rotate-180"
                )}
                aria-hidden="true"
              />
            </button>

            <div
              id={`nav-group-${group.label}`}
              className={cn(
                "overflow-hidden transition-all duration-300 ease-in-out",
                isGroupCollapsed(group.label) ? "max-h-0 opacity-0" : "max-h-96 opacity-100"
              )}
              role="group"
              aria-label={`${group.label} navigation items`}
            >
              <div className="pl-7 mt-1 space-y-1">
                {group.items.map((item) => {
                  const isActive = isItemActive(item);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 text-sm rounded-lg transition-all duration-150",
                        "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-surface",
                        isActive
                          ? "bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300"
                          : "text-text-secondary hover:bg-hover hover:text-text-primary"
                      )}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <Icon className={cn("h-4 w-4 flex-shrink-0", isActive ? "text-primary-500" : "text-text-muted")} />
                      <span className="flex-1 truncate font-medium">{item.name}</span>
                      {isActive && <ChevronRight className="h-4 w-4 text-primary-500" aria-hidden="true" />}
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t p-4 bg-surface/30">
        <div className="flex items-center gap-2 px-3 py-2 text-xs text-text-muted hover:text-text-secondary transition-colors rounded-lg">
          <Keyboard className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span className="truncate">Press ? for shortcuts</span>
        </div>

        <button
          onClick={handleLogout}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors mt-3",
            "text-text-secondary hover:bg-danger-50 hover:text-danger-600 dark:hover:bg-danger-900/30",
            "focus:outline-none focus:ring-2 focus:ring-danger-500 focus:ring-offset-2 focus:ring-offset-surface"
          )}
        >
          <LogOut className="h-4 w-4 text-danger-500" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
