// Location: frontend/app/app/dashboard/page.tsx
"use client";

import { useAuth } from "@/hooks/useAuth";

export default function DashboardPage() {
    const { user } = useAuth();

    return (
        <div>
            <h1 className="text-3xl font-bold mb-4">
                Welcome, {user?.username || "User"}!
            </h1>
            <p className="text-muted-foreground">
                This is your dashboard. In the next stage, the "New Experiment" form will
                live here.
            </p>
        </div>
    );
}