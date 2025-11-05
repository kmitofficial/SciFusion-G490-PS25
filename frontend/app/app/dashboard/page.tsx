// Location: frontend/app/app/dashboard/page.tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Slider } from "@/components/ui/slider";
import {
    CODE_MODEL_OPTIONS,
    EXPERIMENT_OPTIONS,
    MODEL_OPTIONS,
} from "@/lib/constants";
import { Sparkles, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// Updated schema: skip_novelty_check → novelty_check (true = skip)
const formSchema = z.object({
    topic: z.string().min(10, { message: "Topic must be at least 10 characters." }).optional().or(z.literal("")),
    experiment: z.string().optional().or(z.literal("")),
    model: z.string().optional().or(z.literal("")),
    code_model: z.string().optional().or(z.literal("")),
    num_ideas: z.number().min(1).max(5),
    rag: z.boolean().default(true),
    check_similarity: z.boolean().default(true),
    novelty_check: z.boolean().default(false), // true = skip novelty check
});

type FormValues = z.infer<typeof formSchema>;

export default function DashboardPage() {
    const router = useRouter();
    const { token } = useAuth();
    const { toast } = useToast();

    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            topic: "",
            experiment: "",
            model: "",
            code_model: "",
            num_ideas: 3,
            rag: true,
            check_similarity: true,
            novelty_check: false, // unchecked by default
        },
    });

    const isLoading = form.formState.isSubmitting;

    async function onSubmit(values: FormValues) {
        console.log("Form Values:", values);
        if (!token) {
            toast({
                title: "Authentication Error",
                description: "You must be logged in to start an experiment.",
                variant: "destructive",
            });
            return;
        }

        // Clean empty strings to null for backend
        const cleanedValues = {
            ...values,
            topic: values.topic || null,
            experiment: values.experiment || null,
            model: values.model || null,
            code_model: values.code_model || null,
        };

        try {
            const response = await api.post("/jobs/", cleanedValues, token);
            const { job_id } = response;
            toast({
                title: "Experiment Started!",
                description: `Job ${job_id} is now running.`,
            });
            router.push(`/app/experiment/${job_id}`);
        } catch (error) {
            console.error("Failed to start job", error);
            toast({
                title: "Error Starting Job",
                description: error instanceof Error ? error.message : "An unknown error occurred.",
                variant: "destructive",
            });
        }
    }

    return (
        <div className="relative min-h-screen w-full bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white flex items-center justify-center p-6 overflow-hidden">
            {/* Animated background gradient orbs */}
            <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-indigo-500/20 to-purple-600/20 rounded-full blur-3xl animate-pulse" />
            <div className="absolute top-32 left-0 w-32 h-32 bg-gradient-to-br from-cyan-500/15 to-blue-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '0.5s' }} />
            <div className="absolute bottom-32 right-0 w-36 h-36 bg-gradient-to-br from-purple-500/15 to-pink-600/15 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
            <div className="absolute bottom-0 left-0 w-44 h-44 bg-gradient-to-br from-violet-500/20 to-fuchsia-600/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1.5s' }} />
           
            {/* Subtle gradient overlay for depth */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-indigo-950/10" />
            <div className="relative z-10 max-w-3xl w-full">
                {/* Header */}
                <div className="mb-8 text-center">
                    <div className="flex items-center justify-center gap-3 mb-3">
                        <div className="relative">
                            <Sparkles className="h-7 w-7 text-indigo-400 animate-pulse" />
                            <div className="absolute inset-0 h-7 w-7 text-indigo-400 blur-sm opacity-50">
                                <Sparkles className="h-7 w-7" />
                            </div>
                        </div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                            Start a New Experiment
                        </h1>
                    </div>
                    <p className="text-sm text-indigo-300/60 font-medium tracking-wide">
                        Configure your research parameters and launch AI-powered experiments
                    </p>
                </div>

                {/* Form Card */}
                <div className="rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-gray-900/80 via-gray-900/60 to-gray-900/80 backdrop-blur-sm p-8 shadow-2xl">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                            {/* Topic */}
                            <FormField
                                control={form.control}
                                name="topic"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-indigo-300 font-semibold">Research Topic</FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="e.g., Using transformers for time series forecasting"
                                                {...field}
                                                className="bg-white/5 border-white/10 text-white placeholder:text-white/30 focus:border-indigo-400/50 transition-all"
                                            />
                                        </FormControl>
                                        <FormDescription className="text-xs text-indigo-300/60">
                                            The main research area or question.
                                        </FormDescription>
                                        <FormMessage className="text-red-400 text-xs" />
                                    </FormItem>
                                )}
                            />

                            {/* Experiment Type */}
                            <FormField
                                control={form.control}
                                name="experiment"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-indigo-300 font-semibold">Experiment Type</FormLabel>
                                        <Select onValueChange={field.onChange} value={field.value}>
                                            <FormControl>
                                                <SelectTrigger className="bg-white/5 border-white/10 text-white data-[placeholder]:text-white/30 focus:border-indigo-400/50">
                                                    <SelectValue placeholder="Select an experiment..." />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent className="bg-gray-900 border-indigo-500/30 text-white">
                                                {EXPERIMENT_OPTIONS.map((opt) => (
                                                    <SelectItem key={opt.value} value={opt.value} className="hover:bg-indigo-500/20">
                                                        {opt.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <FormDescription className="text-xs text-indigo-300/60">
                                            The baseline experiment to run against.
                                        </FormDescription>
                                        <FormMessage className="text-red-400 text-xs" />
                                    </FormItem>
                                )}
                            />

                            {/* Models */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <FormField
                                    control={form.control}
                                    name="model"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-indigo-300 font-semibold">Research Model</FormLabel>
                                            <Select onValueChange={field.onChange} value={field.value}>
                                                <FormControl>
                                                    <SelectTrigger className="bg-white/5 border-white/10 text-white data-[placeholder]:text-white/30 focus:border-indigo-400/50">
                                                        <SelectValue placeholder="Select a model..." />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent className="bg-gray-900 border-indigo-500/30 text-white">
                                                    {MODEL_OPTIONS.map((opt) => (
                                                        <SelectItem key={opt.value} value={opt.value} className="hover:bg-indigo-500/20">
                                                            {opt.label}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                            <FormDescription className="text-xs text-indigo-300/60">Used for idea generation.</FormDescription>
                                            <FormMessage className="text-red-400 text-xs" />
                                        </FormItem>
                                    )}
                                />
                                <FormField
                                    control={form.control}
                                    name="code_model"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="text-indigo-300 font-semibold">Code Model</FormLabel>
                                            <Select onValueChange={field.onChange} value={field.value}>
                                                <FormControl>
                                                    <SelectTrigger className="bg-white/5 border-white/10 text-white data-[placeholder]:text-white/30 focus:border-indigo-400/50">
                                                        <SelectValue placeholder="Select a code model..." />
                                                    </SelectTrigger>
                                                </FormControl>
                                                <SelectContent className="bg-gray-900 border-indigo-500/30 text-white">
                                                    {CODE_MODEL_OPTIONS.map((opt) => (
                                                        <SelectItem key={opt.value} value={opt.value} className="hover:bg-indigo-500/20">
                                                            {opt.label}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                            <FormDescription className="text-xs text-indigo-300/60">Used for code generation.</FormDescription>
                                            <FormMessage className="text-red-400 text-xs" />
                                        </FormItem>
                                    )}
                                />
                            </div>

                            {/* Num Ideas */}
                            <FormField
                                control={form.control}
                                name="num_ideas"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="text-indigo-300 font-semibold">Number of Ideas (1-5)</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center gap-4">
                                                <Slider
                                                    min={1}
                                                    max={5}
                                                    step={1}
                                                    value={[field.value]}
                                                    onValueChange={(vals) => field.onChange(vals[0])}
                                                    className="flex-1"
                                                />
                                                <span className="flex h-10 w-12 items-center justify-center rounded-lg bg-gradient-to-r from-indigo-500/30 to-purple-500/30 text-indigo-200 font-bold border border-indigo-400/30 shadow-sm">
                                                    {field.value}
                                                </span>
                                            </div>
                                        </FormControl>
                                        <FormMessage className="text-red-400 text-xs" />
                                    </FormItem>
                                )}
                            />

                            {/* Checkboxes */}
                            <div className="space-y-4">
                                <FormField
                                    control={form.control}
                                    name="rag"
                                    render={({ field }) => (
                                        <FormItem className="flex flex-row items-center justify-between rounded-xl border border-white/10 p-4 bg-white/5 hover:bg-white/10 transition-all backdrop-blur-sm">
                                            <div className="space-y-0.5">
                                                <FormLabel className="text-white font-semibold">Enable RAG</FormLabel>
                                                <FormDescription className="text-xs text-indigo-300/60">
                                                    Use Retrieval-Augmented Generation for better ideas.
                                                </FormDescription>
                                            </div>
                                            <FormControl>
                                                <Checkbox
                                                    checked={field.value}
                                                    onCheckedChange={field.onChange}
                                                    className="data-[state=checked]:bg-indigo-500 data-[state=checked]:border-indigo-500"
                                                />
                                            </FormControl>
                                        </FormItem>
                                    )}
                                />
                                <FormField
                                    control={form.control}
                                    name="check_similarity"
                                    render={({ field }) => (
                                        <FormItem className="flex flex-row items-center justify-between rounded-xl border border-white/10 p-4 bg-white/5 hover:bg-white/10 transition-all backdrop-blur-sm">
                                            <div className="space-y-0.5">
                                                <FormLabel className="text-white font-semibold">Check Similarity</FormLabel>
                                                <FormDescription className="text-xs text-indigo-300/60">
                                                    Ensure generated ideas are novel.
                                                </FormDescription>
                                            </div>
                                            <FormControl>
                                                <Checkbox
                                                    checked={field.value}
                                                    onCheckedChange={field.onChange}
                                                    className="data-[state=checked]:bg-indigo-500 data-[state=checked]:border-indigo-500"
                                                />
                                            </FormControl>
                                        </FormItem>
                                    )}
                                />
                                <FormField
    control={form.control}
    name="novelty_check"
    render={({ field }) => {
        // Invert the value for the UI
        const isChecked = !field.value; // true = skip (checked), false = run (unchecked)

        return (
            <FormItem className="flex flex-row items-center justify-between rounded-xl border border-white/10 p-4 bg-white/5 hover:bg-white/10 transition-all backdrop-blur-sm">
                <div className="space-y-0.5">
                    <FormLabel className="text-white font-semibold">
                        Novelty Check
                    </FormLabel>
                    <FormDescription className="text-xs text-indigo-300/60">
                        Novelty check will be done.
                    </FormDescription>
                </div>
                <FormControl>
                    <Checkbox
                        checked={isChecked}
                        onCheckedChange={(checked) => {
                            // Invert back when sending to form state
                            field.onChange(!checked);
                        }}
                        className="data-[state=checked]:bg-red-500 data-[state=checked]:border-red-500 border-white/20"
                    />
                </FormControl>
            </FormItem>
        );
    }}
/>
                            </div>

                            {/* Submit Button */}
                            <Button
                                type="submit"
                                size="lg"
                                disabled={isLoading}
                                className={cn(
                                    "w-full h-12 text-lg font-bold transition-all duration-300",
                                    isLoading
                                        ? "bg-gradient-to-r from-indigo-500/50 to-purple-600/50 cursor-not-allowed"
                                        : "bg-gradient-to-r from-indigo-500/90 to-purple-600/90 hover:from-indigo-500 hover:to-purple-600 shadow-lg shadow-indigo-500/50 hover:shadow-indigo-500/60 hover:scale-[1.02] border border-indigo-400/50"
                                )}
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                        Starting...
                                    </>
                                ) : (
                                    <>
                                        <Sparkles className="mr-2 h-5 w-5" />
                                        Start Experiment
                                    </>
                                )}
                            </Button>
                        </form>
                    </Form>
                </div>
            </div>
        </div>
    );
}