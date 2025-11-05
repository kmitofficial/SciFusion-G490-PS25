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
import { FilePlus, Loader2, LogOut, Sparkles } from "lucide-react";

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
                    setLoadError("We couldn't load your experiment history.");
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
        <div className="relative w-72 h-full bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white p-5 flex flex-col border-r border-indigo-500/20 overflow-hidden shadow-2xl">
            {/* Background gradient orbs */}
            <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-full blur-3xl animate-pulse" />
            <div className="absolute top-32 left-0 w-32 h-32 bg-gradient-to-br from-cyan-500/15 to-blue-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '0.5s' }} />
            <div className="absolute bottom-32 right-0 w-36 h-36 bg-gradient-to-br from-purple-500/15 to-pink-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
            <div className="absolute bottom-0 left-0 w-44 h-44 bg-gradient-to-br from-violet-500/20 to-fuchsia-600/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1.5s' }} />

            {/* Subtle overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-indigo-950/10" />

            {/* Content */}
            <div className="relative z-10 flex flex-col h-full">

                {/* Header */}
                <div className="mb-8 pb-6 border-b border-gradient-to-r from-transparent via-indigo-500/30 to-transparent">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="relative">
                            <Sparkles className="h-6 w-6 text-indigo-400 animate-pulse" />
                            <div className="absolute inset-0 h-6 w-6 text-indigo-400 blur-sm opacity-50">
                                <Sparkles className="h-6 w-6" />
                            </div>
                        </div>
                        <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                            SciFusion
                        </h2>
                    </div>
                    <p className="text-xs text-indigo-300/60 ml-9 font-medium tracking-wide">Research Intelligence Platform</p>
                </div>

                {/* Main Navigation */}
                <nav className="space-y-3 mb-8">
                    <Button
                        variant="ghost"
                        className={cn(
                            "w-full justify-start gap-3 font-semibold transition-all duration-300 border h-11 backdrop-blur-sm",
                            pathname === "/app/dashboard"
                                ? "bg-gradient-to-r from-indigo-500/90 to-purple-600/90 text-white shadow-lg shadow-indigo-500/50 hover:shadow-indigo-500/60 hover:from-indigo-500 hover:to-purple-600 scale-[1.02] border-indigo-400/50"
                                : "bg-white/5 text-white/90 hover:bg-gradient-to-r hover:from-indigo-500/20 hover:to-purple-500/20 hover:text-white hover:scale-[1.02] border-white/10 hover:border-indigo-400/40"
                        )}
                        asChild
                    >
                        <Link href="/app/dashboard">
                            <FilePlus className="h-4 w-4" /> 
                            <span>New Experiment</span>
                        </Link>
                    </Button>
                </nav>

                {/* Job History - Scrollable */}
                <div className="flex-1 min-h-0">
                    <ScrollArea className="h-full">
                        <nav className="space-y-2 pr-4">
                            {isLoading && (
                                <div className="flex flex-col justify-center items-center p-8 gap-3 bg-gradient-to-br from-white/5 to-white/0 rounded-xl border border-white/10">
                                    <Loader2 className="h-6 w-6 animate-spin text-indigo-400" />
                                    <p className="text-xs text-indigo-300/70 font-medium">Loading experiments...</p>
                                </div>
                            )}
                            {!isLoading && !loadError && jobs.length === 0 && (
                                <div className="text-center p-8 bg-gradient-to-br from-white/5 to-white/0 rounded-xl border border-white/10 backdrop-blur-sm">
                                    <div className="bg-gradient-to-br from-indigo-500/20 to-purple-500/20 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-3 border border-indigo-400/30">
                                        <FilePlus className="h-8 w-8 text-indigo-300" />
                                    </div>
                                    <p className="text-sm text-white/70 font-medium mb-1">No experiments yet</p>
                                    <p className="text-xs text-white/40">Create your first one to get started!</p>
                                </div>
                            )}
                            {loadError && (
                                <div className="p-4 bg-gradient-to-br from-red-500/20 to-red-600/20 border border-red-400/40 rounded-xl backdrop-blur-sm">
                                    <p className="text-xs text-red-300 font-medium">{loadError}</p>
                                </div>
                            )}
                            {jobs.map((job) => {
                                const jobId = job._id ?? job.id;
                                if (!jobId) return null;
                                const isActive = pathname === `/app/experiment/${jobId}`;
                                const topic = job.request?.topic ?? "Untitled experiment";
                                return (
                                    <Link
                                        key={jobId}
                                        href={`/app/experiment/${jobId}`}
                                        className={cn(
                                            "block p-3 ml-0.5 rounded-xl transition-all duration-300 group backdrop-blur-sm flex flex-col justify-between",
                                            isActive
                                                ? "bg-gradient-to-br from-indigo-500/40 to-purple-600/40 border-2 border-indigo-400/60 text-white shadow-lg shadow-indigo-500/30 scale-[1.02]"
                                                : "bg-gradient-to-br from-white/5 to-white/0 text-white/80 hover:bg-gradient-to-br hover:from-indigo-500/15 hover:to-purple-500/15 hover:text-white border border-white/10 hover:border-indigo-500/40 hover:scale-[1.01] hover:shadow-md"
                                        )}
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <p
                                                className={cn(
                                                    "text-sm font-semibold line-clamp-1 flex-1",
                                                    isActive ? "text-white" : "text-white/90"
                                                )}
                                                title={topic}
                                            >
                                                {topic}
                                            </p>
                                            {isActive && (
                                                <span className="flex h-2 w-2 mt-1">
                                                    <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-indigo-300 opacity-75"></span>
                                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-400 shadow-sm shadow-indigo-400/50"></span>
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center justify-between mt-2">
                                            <p
                                                className={cn(
                                                    "text-xs font-medium",
                                                    isActive ? "text-indigo-200/80" : "text-white/50"
                                                )}
                                            >
                                                {job.created_at ? formatDate(job.created_at) : "Recently"}
                                            </p>
                                            <span
                                                className={cn(
                                                    "text-xs px-2.5 py-0.5 rounded-full font-semibold border",
                                                    job.status === "completed"
                                                        ? "bg-gradient-to-r from-green-500/30 to-emerald-500/30 text-green-300 border-green-400/40"
                                                        : job.status === "running"
                                                        ? "bg-gradient-to-r from-blue-500/30 to-cyan-500/30 text-blue-300 border-blue-400/40"
                                                        : "bg-gradient-to-r from-yellow-500/30 to-amber-500/30 text-yellow-300 border-yellow-400/40"
                                                )}
                                            >
                                                {job.status}
                                            </span>
                                        </div>
                                    </Link>
                                );
                            })}
                        </nav>
                    </ScrollArea>
                </div>

                {/* User Info & Logout */}
                {user && (
                    <div className="mt-auto pt-6 border-t border-gradient-to-r from-transparent via-indigo-500/30 to-transparent">
                        <div className="mb-3 p-4 bg-gradient-to-br from-white/10 to-white/5 rounded-xl border border-white/20 hover:bg-gradient-to-br hover:from-white/15 hover:to-white/10 transition-all duration-300 backdrop-blur-sm shadow-lg">
                            <p className="text-sm font-semibold text-white flex items-center gap-2.5 mb-1">
                                <span className="relative flex h-2.5 w-2.5">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-400 shadow-sm shadow-green-400/50"></span>
                                </span>
                                {user.username}
                            </p>
                            <p className="text-xs text-indigo-200/60 ml-5">{user.email}</p>
                        </div>
                        <Button
                            variant="ghost"
                            className="w-full justify-start gap-3 bg-gradient-to-r from-white/5 to-white/0 text-white/90 hover:bg-gradient-to-r hover:from-red-500/30 hover:to-pink-500/30 hover:text-red-200 transition-all duration-300 border border-white/10 hover:border-red-400/40 h-11 font-semibold backdrop-blur-sm"
                            onClick={logout}
                        >
                            <LogOut className="h-4 w-4" />
                            <span>Log Out</span>
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}
