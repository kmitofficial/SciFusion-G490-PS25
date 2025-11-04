// Location: frontend/app/app/layout.tsx
"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import Sidebar from "./components/sidebar";

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
        // You can replace this with a proper loading spinner
        return (
            <div className="flex items-center justify-center min-h-screen">
                Loading...
            </div>
        );
    }

    // User is authenticated, render the app layout
    return (
        <div className="flex h-screen">
            <Sidebar />
            <main className="flex-1 p-6 overflow-y-auto">{children}</main>
        </div>
    );
}