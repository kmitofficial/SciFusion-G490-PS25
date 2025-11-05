// Location: frontend/app/page.tsx
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function IntroPage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-8">
            <div className="text-center space-y-6">
                <h1 className="text-5xl font-bold">Welcome to SciFusion</h1>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                    Your AI-powered partner for accelerating scientific discovery.
                    Automate literature reviews, generate novel ideas, and run experiments
                    all in one place.
                </p>
                <div className="flex justify-center gap-4">
                    <Button asChild size="lg">
                        <Link href="/login">Login</Link>
                    </Button>
                    <Button asChild size="lg" variant="outline">
                        <Link href="/signup">Sign Up</Link>
                    </Button>
                </div>
            </div>
        </div>
    );
}