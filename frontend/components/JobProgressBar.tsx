// Location: frontend/components/JobProgressBar.tsx
"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "./ui/card";
import { Progress } from "./ui/progress";

interface JobProgressBarProps {
    completed: number;
    total: number;
}

export function JobProgressBar({ completed, total }: JobProgressBarProps) {
    const percent = total > 0 ? (completed / total) * 100 : 0;

    let title = "Waiting for experiments to be finalized...";
    if (total > 0) {
        title = `Processing ${total} novel ideas...`;
    }
    if (completed === total && total > 0) {
        title = "All experiments complete!";
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Overall Experiment Progress</CardTitle>
                <CardDescription>{title}</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="flex items-center gap-4">
                    <Progress value={percent} className="flex-1" />
                    <span className="font-mono text-lg">
            {completed} / {total}
          </span>
                </div>
            </CardContent>
        </Card>
    );
}