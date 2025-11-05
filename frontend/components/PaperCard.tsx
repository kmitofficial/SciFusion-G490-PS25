// Location: frontend/components/PaperCard.tsx
"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Paper } from "@/lib/types";
import { Info, BookText, Star } from "lucide-react";

interface PaperCardProps {
    paper: Paper;
}

export function PaperCard({ paper }: PaperCardProps) {
    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle className="text-lg">{paper.title}</CardTitle>
                <CardDescription>
                    {paper.tldr || "TLDR not available."}
                </CardDescription>
            </CardHeader>
            <CardFooter className="flex justify-between items-center">
                <div className="flex gap-2">
                    <Badge variant="outline">Year: {paper.year}</Badge>
                    <Badge variant="default">Score: {paper.score}</Badge>
                </div>

                <Dialog>
                    <DialogTrigger asChild>
                        <Button variant="ghost" size="icon">
                            <Info className="h-4 w-4" />
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-2xl">
                        <DialogHeader>
                            <DialogTitle>{paper.title}</DialogTitle>
                            <DialogDescription>
                                <div className="flex gap-4 my-2">
                                    <Badge variant="outline">Year: {paper.year}</Badge>
                                    <Badge variant="default">Score: {paper.score}</Badge>
                                    <Badge variant="secondary">
                                        Citations: {paper.citationCount}
                                    </Badge>
                                </div>
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                            <div className="space-y-1">
                                <h4 className="font-semibold flex items-center gap-2">
                                    <Star className="h-4 w-4" /> TL;DR
                                </h4>
                                <p className="text-sm text-muted-foreground">
                                    {paper.tldr || "Not available."}
                                </p>
                            </div>
                            <div className="space-y-1">
                                <h4 className="font-semibold flex items-center gap-2">
                                    <BookText className="h-4 w-4" /> Abstract
                                </h4>
                                <p className="text-sm text-muted-foreground">
                                    {paper.abstract}
                                </p>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>
            </CardFooter>
        </Card>
    );
}