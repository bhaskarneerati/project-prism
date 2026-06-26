"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (pathname === "/admin/login") {
      setChecked(true);
      return;
    }
    const token = localStorage.getItem("admin_token");
    if (!token) {
      router.push("/admin/login");
    } else {
      setChecked(true);
    }
  }, [router, pathname]);

  function handleLogout() {
    localStorage.removeItem("admin_token");
    router.push("/admin/login");
  }

  if (!checked) {
    return null;
  }

  return (
    <div className="flex h-full flex-1 flex-col overflow-hidden">
      {pathname !== "/admin/login" && (
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4 dark:border-slate-800 dark:bg-slate-950">
          <span className="text-lg font-semibold text-slate-900 dark:text-slate-50">
            Prism Admin
          </span>
          <Button variant="outline" onClick={handleLogout}>
            Logout
          </Button>
        </header>
      )}
      <main className="flex-1 overflow-y-auto bg-slate-50 p-8 dark:bg-slate-900">{children}</main>
    </div>
  );
}
