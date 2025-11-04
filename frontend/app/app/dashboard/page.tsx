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

// Define the form schema using Zod, based on ResearchRequest
const formSchema = z.object({
    topic: z
        .string()
        .min(10, { message: "Topic must be at least 10 characters." }),
    experiment: z.string({ required_error: "Please select an experiment." }),
    model: z.string({ required_error: "Please select a model." }),
    code_model: z.string({ required_error: "Please select a code model." }),
    num_ideas: z.number().min(1).max(5),
    rag: z.boolean().default(true),
    check_similarity: z.boolean().default(true),
    skip_novelty_check: z.boolean().default(false),
});

type FormValues = z.infer<typeof formSchema>;

export default function DashboardPage() {
    const router = useRouter();
    const { token } = useAuth();
    const { toast } = useToast();

    // 1. Define your form.
    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            topic: "novel attention mechanisms for sentiment classification",
            experiment: "sentiment_classification_sst2",
            model: "gemini-2.5-flash-lite",
            code_model: "flash",
            num_ideas: 3,
            rag: true,
            check_similarity: true,
            skip_novelty_check: false,
        },
    });

    const isLoading = form.formState.isSubmitting;

    // 2. Define a submit handler.
    async function onSubmit(values: FormValues) {
        if (!token) {
            toast({
                title: "Authentication Error",
                description: "You must be logged in to start an experiment.",
                variant: "destructive",
            });
            return;
        }

        try {
            const response = await api.post("/jobs/", values, token);
            const { job_id } = response;

            toast({
                title: "Experiment Started!",
                description: `Job ${job_id} is now running.`,
            });

            // 3. Navigate to the new experiment page
            router.push(`/app/experiment/${job_id}`);
        } catch (error) {
            console.error("Failed to start job", error);
            toast({
                title: "Error Starting Job",
                description:
                    error instanceof Error ? error.message : "An unknown error occurred.",
                variant: "destructive",
            });
        }
    }

    return (
        <div className="max-w-3xl mx-auto">
            <h1 className="text-3xl font-bold mb-6">Start a New Experiment</h1>
            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                    {/* Topic */}
                    <FormField
                        control={form.control}
                        name="topic"
                        render={({ field }) => (
                            <FormItem>
                                <FormLabel>Research Topic</FormLabel>
                                <FormControl>
                                    <Input
                                        placeholder="e.g., Using transformers for time series forecasting"
                                        {...field}
                                    />
                                </FormControl>
                                <FormDescription>
                                    The main research area or question.
                                </FormDescription>
                                <FormMessage />
                            </FormItem>
                        )}
                    />

                    {/* Experiment Type */}
                    <FormField
                        control={form.control}
                        name="experiment"
                        render={({ field }) => (
                            <FormItem>
                                <FormLabel>Experiment Type</FormLabel>
                                <Select
                                    onValueChange={field.onChange}
                                    defaultValue={field.value}
                                >
                                    <FormControl>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select an experiment..." />
                                        </SelectTrigger>
                                    </FormControl>
                                    <SelectContent>
                                        {EXPERIMENT_OPTIONS.map((opt) => (
                                            <SelectItem key={opt.value} value={opt.value}>
                                                {opt.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <FormDescription>
                                    The baseline experiment to run against.
                                </FormDescription>
                                <FormMessage />
                            </FormItem>
                        )}
                    />

                    {/* Models */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <FormField
                            control={form.control}
                            name="model"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Research Model</FormLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        defaultValue={field.value}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select a model..." />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {MODEL_OPTIONS.map((opt) => (
                                                <SelectItem key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormDescription>Used for idea generation.</FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="code_model"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Code Model</FormLabel>
                                    <Select
                                        onValueChange={field.onChange}
                                        defaultValue={field.value}
                                    >
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select a code model..." />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {CODE_MODEL_OPTIONS.map((opt) => (
                                                <SelectItem key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormDescription>Used for code generation.</FormDescription>
                                    <FormMessage />
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
                                <FormLabel>Number of Ideas (1-5)</FormLabel>
                                <FormControl>
                                    <div className="flex items-center gap-4">
                                        <Slider
                                            min={1}
                                            max={5}
                                            step={1}
                                            value={[field.value]}
                                            onValueChange={(vals) => field.onChange(vals[0])}
                                            className="w-full"
                                        />
                                        <span className="p-2 w-12 text-center rounded-md bg-secondary">
                      {field.value}
                    </span>
                                    </div>
                                </FormControl>
                                <FormMessage />
                            </FormItem>
                        )}
                    />

                    {/* Checkboxes */}
                    <div className="space-y-4">
                        <FormField
                            control={form.control}
                            name="rag"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel>Enable RAG</FormLabel>
                                        <FormDescription>
                                            Use Retrieval-Augmented Generation for better ideas.
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Checkbox
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="check_similarity"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel>Check Similarity</FormLabel>
                                        <FormDescription>
                                            Ensure generated ideas are novel.
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Checkbox
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="skip_novelty_check"
                            render={({ field }) => (
                                <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                                    <div className="space-y-0.5">
                                        <FormLabel>Skip Novelty Check</FormLabel>
                                        <FormDescription>
                                            (Debug) Skip the novelty check phase.
                                        </FormDescription>
                                    </div>
                                    <FormControl>
                                        <Checkbox
                                            checked={field.value}
                                            onCheckedChange={field.onChange}
                                        />
                                    </FormControl>
                                </FormItem>
                            )}
                        />
                    </div>

                    <Button type="submit" size="lg" disabled={isLoading}>
                        {isLoading ? "Starting..." : "Start Experiment"}
                    </Button>
                </form>
            </Form>
        </div>
    );
}