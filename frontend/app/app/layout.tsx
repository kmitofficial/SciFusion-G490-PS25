// Location: frontend/app/app/layout.tsx
"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import Sidebar from "./components/sidebar"; // Keep the import

export default function AppLayout({
                                      children,
                                  }: {
    children: React.ReactNode;
}) {
    const { isAuthenticated, isLoading } = useAuth();
    const router = useRouter();

    React.useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            router.replace("/login");
        }
    }, [isAuthenticated, isLoading, router]);

    if (isLoading || !isAuthenticated) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                Loading...
            </div>
        );
    }

    // User is authenticated, render the app layout
    return (
        <div className="flex h-screen">
            {/* The Sidebar is now part of the layout *here*.
        The 'children' (our pages) will render in the 'main' tag.
        This ensures the Sidebar is always present.
      */}
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
                {/* We REMOVE the padding `p-6` from here.
          The child pages (dashboard, experiment) will
          control their own padding.
        */}
                {children}
            </main>
        </div>
    );
}