"use client";

import { useMemo } from "react";
import { ChevronDown, ChevronRight, FileText, Folder, FolderOpen } from "lucide-react";
import { ArtifactNode } from "@/lib/types";
import { cn } from "@/lib/utils";

interface FileTreeProps {
    root: ArtifactNode | null;
    expandedPaths: Set<string>;
    onToggle: (path: string) => void;
    onSelectFile: (path: string) => void;
    selectedFile?: string | null;
}

interface TreeItemProps {
    node: ArtifactNode;
    depth: number;
    expandedPaths: Set<string>;
    onToggle: (path: string) => void;
    onSelectFile: (path: string) => void;
    selectedFile?: string | null;
}

const getNodeKey = (node: ArtifactNode) => {
    if (node.path && node.path.length > 0) {
        return node.path;
    }
    return node.name || "/";
};

const TreeItem = ({
    node,
    depth,
    expandedPaths,
    onToggle,
    onSelectFile,
    selectedFile,
}: TreeItemProps) => {
    const key = useMemo(() => getNodeKey(node), [node]);
    const isExpanded = expandedPaths.has(key);
    const isFile = node.type === "file";
    const isSelected = isFile && selectedFile === node.path;

    const handleToggle = () => {
        onToggle(key);
    };

    const handleSelect = () => {
        if (isFile) {
            onSelectFile(node.path);
        } else {
            handleToggle();
        }
    };

    return (
        <div>
            <button
                type="button"
                onClick={handleSelect}
                className={cn(
                    "flex w-full items-center gap-2 rounded-md px-2 py-1 text-sm transition",
                    isSelected ? "bg-primary/10 text-primary" : "hover:bg-muted"
                )}
                style={{ paddingLeft: `${depth * 14}px` }}
            >
                {node.type === "directory" ? (
                    <span className="flex items-center gap-2">
                        {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                        ) : (
                            <ChevronRight className="h-4 w-4" />
                        )}
                        {isExpanded ? (
                            <FolderOpen className="h-4 w-4 text-primary" />
                        ) : (
                            <Folder className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="text-left font-medium text-muted-foreground">
                            {node.name || "root"}
                        </span>
                    </span>
                ) : (
                    <span className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        <span className="text-left text-muted-foreground">
                            {node.name}
                        </span>
                    </span>
                )}
            </button>

            {node.type === "directory" && isExpanded && node.children && node.children.length > 0 && (
                <div className="flex flex-col">
                    {node.children.map((child) => (
                        <TreeItem
                            key={getNodeKey(child)}
                            node={child}
                            depth={depth + 1}
                            expandedPaths={expandedPaths}
                            onToggle={onToggle}
                            onSelectFile={onSelectFile}
                            selectedFile={selectedFile}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export const FileTree = ({ root, expandedPaths, onToggle, onSelectFile, selectedFile }: FileTreeProps) => {
    if (!root) {
        return (
            <div className="rounded-lg border border-dashed border-muted-foreground/40 p-6 text-center text-sm text-muted-foreground">
                No artifacts available for this experiment yet.
            </div>
        );
    }

    return (
        <div className="space-y-1">
            <TreeItem
                node={root}
                depth={0}
                expandedPaths={expandedPaths}
                onToggle={onToggle}
                onSelectFile={onSelectFile}
                selectedFile={selectedFile}
            />
        </div>
    );
};
