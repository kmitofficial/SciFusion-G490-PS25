// Location: frontend/app/app/components/sidebar.tsx
"use client";

import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";

export default function Sidebar() {
    const { user, logout } = useAuth();

    return (
        <div className="w-64 h-full bg-secondary text-secondary-foreground p-4 flex flex-col">
            <div className="mb-4">
                <h2 className="text-2xl font-bold">SciFusion</h2>
            </div>

            {/* Job history will go here in Stage 4 */}
            <nav className="flex-1 space-y-2">
                <p className="text-sm text-muted-foreground">My Experiments</p>
                <p className="text-sm">(History will be here)</p>
            </nav>

            {/* User Info & Logout */}
            {user && (
                <div className="mt-auto">
                    <div className="mb-2">
                        <p className="text-sm font-medium">{user.username}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                    <Button variant="ghost" className="w-full justify-start" onClick={logout}>
                        Log Out
                    </Button>
                </div>
            )}
        </div>
    );
}