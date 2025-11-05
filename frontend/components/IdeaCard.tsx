// Location: frontend/components/IdeaCard.tsx
"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Idea } from "@/lib/types";
import { CheckCircle2, Loader, XCircle } from "lucide-react";

interface IdeaCardProps {
    idea: Idea;
}

export function IdeaCard({ idea }: IdeaCardProps) {
    const result = idea.experiment_result;
    const metrics = result?.metrics;
    const testAccuracy = metrics?.test_accuracy;

    const formatMetric = (key: string, value: any) => {
        let a = key.replace(/_/g, " ");
        a = a.charAt(0).toUpperCase() + a.slice(1);
        let v = typeof value === 'number' ? value.toFixed(4) : String(value);
        return `${a}: ${v}`;
    };

    return (
        <Card className="w-full">
            <CardHeader>
                <div className="flex justify-between items-center">
                    <CardTitle className="text-lg">{idea.title}</CardTitle>
                    <Badge variant="default">Idea Score: {idea.score}</Badge>
                </div>
                <CardDescription>{idea.description}</CardDescription>
            </CardHeader>
            <CardContent>
                <h4 className="font-semibold mb-2">Experiment Result</h4>
                {!result && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                        <Loader className="h-4 w-4 animate-spin" />
                        <span>Experiment in progress...</span>
                    </div>
                )}
                {result && (
                    <Card className="bg-secondary">
                        <CardHeader>
                            <CardTitle className="text-base flex items-center gap-2">
                                {metrics ? (
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                ) : (
                                    <XCircle className="h-5 w-5 text-red-500" />
                                )}
                                Run {result.run_id} - {metrics ? "Completed" : "Failed"}
                            </CardTitle>
                            <CardDescription>
                                Code saved to: {result.code_path}
                            </CardDescription>
                        </CardHeader>
                        {metrics && (
                            <CardContent>
                                <h5 className="font-semibold mb-2">Metrics:</h5>
                                <div className="flex flex-wrap gap-2">
                                    {Object.entries(metrics).map(([key, value]) => (
                                        <Badge key={key} variant="outline">
                                            {formatMetric(key, value)}
                                        </Badge>
                                    ))}
                                </div>
                            </CardContent>
                        )}
                    </Card>
                )}
            </CardContent>
        </Card>
    );
}