// Location: frontend/components/GroupedExperimentCard.tsx
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
import { GroupedExperiment, ExperimentResult } from "@/lib/types";
import { Progress } from "./ui/progress";
import { cn } from "@/lib/utils";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";

const MAX_RUNS = 5; // From your sample

interface GroupedExperimentCardProps {
    groupedExp: GroupedExperiment;
    baseline: number | null;
}

// Helper to get the primary metric.
// We have to guess the metric based on your sample logic.
const getMetric = (result: ExperimentResult): number | null => {
    try {
        // Attempt 1: From your sample code for SST-2
        let acc = result.metrics?.sentiment?.means?.best_acc;
        if (acc) return parseFloat(acc);

        // Attempt 2: A more generic 'test_accuracy'
        acc = result.metrics?.test_accuracy;
        if (acc) return parseFloat(acc);

        // Attempt 3: A more generic 'test_loss' (lower is better)
        let loss = result.metrics?.test_loss;
        if (loss) return -parseFloat(loss); // Invert so higher is better

        return null;
    } catch (e) {
        return null;
    }
};

export function GroupedExperimentCard({
                                          groupedExp,
                                          baseline,
                                      }: GroupedExperimentCardProps) {
    const { idea, runs } = groupedExp;

    // Find the best run
    const validRuns = runs.filter((r) => r.run_number !== 99);
    const bestRun = [...validRuns].sort(
        (a, b) => (getMetric(b) ?? -Infinity) - (getMetric(a) ?? -Infinity),
    )[0];

    const bestMetric = bestRun ? getMetric(bestRun) : null;

    let comparison: React.ReactNode = null;
    let metricClass = "bg-secondary text-secondary-foreground";
    let Icon = Minus;

    if (bestMetric !== null && baseline !== null) {
        const diff = bestMetric - baseline;
        if (diff > 0.0001) {
            comparison = `+${diff.toFixed(4)} vs Baseline`;
            metricClass = "bg-green-600 text-white";
            Icon = ArrowUp;
        } else if (diff < -0.0001) {
            comparison = `${diff.toFixed(4)} vs Baseline`;
            metricClass = "bg-red-600 text-white";
            Icon = ArrowDown;
        } else {
            comparison = "Matches Baseline";
        }
    }

    const runsCompleted = validRuns.length;
    const runPercent = (runsCompleted / MAX_RUNS) * 100;

    return (
        <Card className="w-full">
            <CardHeader>
                <div className="flex justify-between items-start gap-4">
                    <div>
                        <CardTitle className="text-lg">{idea.Title}</CardTitle>
                        <CardDescription>{idea.Summary}</CardDescription>
                    </div>
                    {bestMetric !== null && (
                        <div
                            className={cn(
                                "p-3 rounded-lg text-center min-w-[120px]",
                                metricClass,
                            )}
                        >
                            <div className="text-2xl font-bold flex items-center justify-center gap-1">
                                <Icon className="h-5 w-5" />
                                {bestMetric.toFixed(4)}
                            </div>
                            <div className="text-xs font-medium">{comparison}</div>
                        </div>
                    )}
                </div>
            </CardHeader>
            <CardContent>
                <h4 className="text-sm font-semibold mb-2">
                    Experiment Runs ({runsCompleted} / {MAX_RUNS})
                </h4>
                <Progress value={runPercent} className="mb-4" />
                <ul className="space-y-1">
                    {validRuns
                        .sort((a, b) => a.run_number - b.run_number)
                        .map((run) => (
                            <li
                                key={run.run_number}
                                className={cn(
                                    "flex justify-between items-center p-2 rounded-md text-sm",
                                    run === bestRun
                                        ? "bg-secondary"
                                        : "bg-secondary/50",
                                )}
                            >
                                <span className="font-medium">Run {run.run_number}</span>
                                <span className="font-mono">
                  {getMetric(run)?.toFixed(4) ?? "N/A"}
                </span>
                            </li>
                        ))}
                </ul>
            </CardContent>
        </Card>
    );
}