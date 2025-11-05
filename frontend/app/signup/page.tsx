// Location: frontend/app/signup/page.tsx
"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { ApiError } from "@/lib/api";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function SignupPage() {
    const [username, setUsername] = React.useState("");
    const [email, setEmail] = React.useState("");
    const [password, setPassword] = React.useState("");
    const [error, setError] = React.useState<string | null>(null);
    const [isLoading, setIsLoading] = React.useState(false);
    const { signup } = useAuth();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            await signup({ username, email, password });
            
            toast.success("Account created successfully!");
            // On success, the auth context handles redirection to /login
        } catch (err) {
            let message = "An unknown error occurred.";
            if (err instanceof ApiError) {
                message = err.message;
            } else if (err instanceof Error) {
                message = err.message;
            }
            setError(message);
            toast.error(message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-black text-white px-4">
            <div className="absolute inset-0">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.25),_transparent_55%)]" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,_rgba(99,102,241,0.35),_transparent_60%)]" />
                <div className="absolute -top-32 right-1/4 h-72 w-72 rounded-full bg-cyan-500/30 blur-3xl" />
                <div className="absolute -bottom-24 left-1/3 h-80 w-80 rounded-full bg-fuchsia-500/20 blur-3xl" />
            </div>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="relative z-10 w-full max-w-md"
            >
                <Card className="border border-white/10 bg-white/5 shadow-2xl backdrop-blur-xl text-white">
                    <form onSubmit={handleSubmit}>
                        <CardHeader className="text-center space-y-2">
                            <CardTitle className="text-3xl font-semibold tracking-tight">
                                Create Account
                            </CardTitle>
                            <CardDescription className="text-sm text-white/70">
                                Enter your information to start your research journey.
                            </CardDescription>
                        </CardHeader>

                        <CardContent className="grid gap-4">
                            {error && (
                                <p className="text-center text-sm font-medium text-red-400">
                                    {error}
                                </p>
                            )}

                            <div className="grid gap-2 mt-3">
                                <Label htmlFor="username">Username</Label>
                                <Input
                                    id="username"
                                    type="text"
                                    placeholder="Enter your username"
                                    required
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    disabled={isLoading}
                                    className="bg-white/10 border-white/20 text-white placeholder-white/60 focus:border-primary focus:ring-2 focus:ring-primary/60"
                                />
                            </div>

                            <div className="grid gap-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="Enter your email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    disabled={isLoading}
                                    className="bg-white/10 border-white/20 text-white placeholder-white/60 focus:border-primary focus:ring-2 focus:ring-primary/60"
                                />
                            </div>

                            <div className="grid gap-2">
                                <Label htmlFor="password">Password</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    required
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    disabled={isLoading}
                                    className="bg-white/10 border-white/20 text-white placeholder-white/60 focus:border-primary focus:ring-2 focus:ring-primary/60"
                                />
                            </div>
                        </CardContent>

                        <CardFooter className="flex flex-col gap-4 mt-5">
                            <Button
                                className="w-full font-medium bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30 border-0 transition-all"
                                type="submit"
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                        Creating account...
                                    </>
                                ) : (
                                    "Sign Up"
                                )}
                            </Button>
                            <div className="text-center text-sm text-white/70">
                                Already have an account?{" "}
                                <Link
                                    href="/login"
                                    className="text-sky-300 hover:text-sky-200 hover:underline font-medium"
                                >
                                    Login
                                </Link>
                            </div>
                        </CardFooter>
                    </form>
                </Card>
            </motion.div>
        </div>
    );
}