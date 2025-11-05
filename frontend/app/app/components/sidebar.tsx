// Location: frontend/app/app/components/sidebar.tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { JobSidebarItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { FilePlus, LayoutDashboard, Loader2, LogOut } from "lucide-react";

// Helper to format the date
const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

export default function Sidebar() {
    const { user, logout, token } = useAuth();
    const pathname = usePathname();
    const [jobs, setJobs] = useState<JobSidebarItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;

        if (!token) {
            setJobs([]);
            setIsLoading(false);
            return () => {
                isMounted = false;
            };
        }

        const load = async (showSpinner = true) => {
            if (!isMounted) return;
            if (showSpinner) {
                setIsLoading(true);
            }
            try {
                const data = await api.get("/jobs/", token);
                if (!isMounted) return;
                if (Array.isArray(data)) {
                    setJobs(data as JobSidebarItem[]);
                } else {
                    setJobs([]);
                }
                setLoadError(null);
            } catch (err) {
                console.error("Failed to fetch jobs:", err);
                if (isMounted) {
                    setLoadError("We couldn’t load your experiment history.");
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        };

        load();

        const interval = setInterval(() => load(false), 10000);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [token]);

    return (
        <div className="w-72 h-full bg-secondary text-secondary-foreground p-4 flex flex-col border-r">
            <div className="mb-4">
                <h2 className="text-2xl font-bold">SciFusion</h2>
            </div>

            {/* Main Navigation */}
            <nav className="space-y-2 mb-4">
                <Button
                    variant={pathname === "/app/dashboard" ? "default" : "ghost"}
                    className="w-full justify-start gap-2"
                    asChild
                >
                    <Link href="/app/dashboard">
                        <FilePlus className="h-4 w-4" /> New Experiment
                    </Link>
                </Button>
            </nav>

            {/* Job History */}
            <div className="flex-1 flex flex-col min-h-0">
                <h3 className="text-sm font-semibold text-muted-foreground px-2 mb-2">
                    My Experiments
                </h3>
                <ScrollArea className="flex-1">
                    <nav className="space-y-1 pr-2">
                        {isLoading && (
                            <div className="flex justify-center items-center p-4">
                                <Loader2 className="h-4 w-4 animate-spin" />
                            </div>
                        )}
                        {!isLoading && !loadError && jobs.length === 0 && (
                            <p className="text-xs text-muted-foreground p-2">
                                No experiments run yet.
                            </p>
                        )}
                        {loadError && (
                            <p className="text-xs text-destructive p-2">
                                {loadError}
                            </p>
                        )}
                        {jobs.map((job) => {
                            const jobId = job._id ?? job.id;
                            if (!jobId) {
                                return null;
                            }
                            const isActive = pathname === `/app/experiment/${jobId}`;
                            const topic = job.request?.topic ?? "Untitled experiment";
                            return (
                                <Link
                                    key={jobId}
                                    href={`/app/experiment/${jobId}`}
                                    className={cn(
                                        "block p-2 rounded-md",
                                        isActive
                                            ? "bg-primary text-primary-foreground"
                                            : "hover:bg-primary/10"
                                    )}
                                >
                                    <p
                                        className="text-sm font-medium truncate"
                                        title={topic}
                                    >
                                        {topic}
                                    </p>
                                    <p
                                        className={cn(
                                            "text-xs",
                                            isActive
                                                ? "text-primary-foreground/80"
                                                : "text-muted-foreground"
                                        )}
                                    >
                                        {job.created_at
                                            ? `${formatDate(job.created_at)} - ${job.status}`
                                            : job.status}
                                    </p>
                                </Link>
                            );
                        })}
                    </nav>
                </ScrollArea>
            </div>

            {/* User Info & Logout */}
            {user && (
                <div className="mt-auto pt-4 border-t">
                    <div className="mb-2 p-2">
                        <p className="text-sm font-medium">{user.username}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                    <Button
                        variant="ghost"
                        className="w-full justify-start gap-2"
                        onClick={logout}
                    >
                        <LogOut className="h-4 w-4" />
                        Log Out
                    </Button>
                </div>
            )}
        </div>
    );
}