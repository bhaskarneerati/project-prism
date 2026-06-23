"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

interface CurrentUser {
  id: string;
  email: string;
}

const NAV_LINKS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/dashboard/api-keys", label: "API Keys" },
  { href: "/dashboard/routes", label: "Routes" },
  { href: "/dashboard/analytics", label: "Analytics" },
  { href: "/dashboard/logs", label: "Logs" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [checked, setChecked] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    } else {
      setChecked(true);
    }
  }, [router]);

  function handleLogout() {
    localStorage.removeItem("token");
    router.push("/login");
  }

  const { data: currentUser } = useQuery<CurrentUser>({
    queryKey: ["auth", "me"],
    queryFn: async () => (await api.get("/v1/auth/me")).data,
    enabled: checked,
  });

  if (!checked) {
    return null;
  }

  return (
    <div className="flex h-full flex-1 overflow-hidden">
      <aside className="flex h-full w-56 shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-6 dark:border-slate-800 dark:bg-slate-950">
        <div className="mb-8 flex items-center justify-between">
          <span className="text-lg font-semibold text-slate-900 dark:text-slate-50">Prism</span>
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
          )}
        </div>
        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
                pathname === link.href &&
                  "bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>
        {currentUser && (
          <p
            className="mb-2 truncate text-xs text-slate-500 dark:text-slate-400"
            title={currentUser.email}
          >
            {currentUser.email}
          </p>
        )}
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </aside>
      <main className="flex-1 overflow-y-auto bg-slate-50 p-8 dark:bg-slate-900">{children}</main>
    </div>
  );
}
