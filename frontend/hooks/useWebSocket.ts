// Location: frontend/hooks/useWebSocket.ts
"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "./useAuth";

const getWebSocketUrl = () => {
    const wsUrl =
        process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";
    return wsUrl;
};

export const useWebSocket = (
    onMessage: (message: any) => void,
    onError: (error: string) => void,
    shouldConnect: boolean = true, // Default to true
    jobId?: string,
) => {
    const { token } = useAuth();
    const ws = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        // --- UPDATED ---
        // Only connect if we have a token AND shouldConnect is true
        if (token && shouldConnect) {
            const query = new URLSearchParams({ token });
            if (jobId) {
                query.append("job_id", jobId);
            }
            const wsUrl = `${getWebSocketUrl()}?${query.toString()}`;
            ws.current = new WebSocket(wsUrl);

            ws.current.onopen = () => {
                console.log("WebSocket connected");
                setIsConnected(true);
            };

            ws.current.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    onMessage(message);
                } catch (e) {
                    console.error("Failed to parse WebSocket message:", e);
                    onMessage({ type: "LOG", data: event.data });
                }
            };

            ws.current.onerror = (event) => {
                console.error("WebSocket error:", event);
                onError("WebSocket connection error.");
                setIsConnected(false);
            };

            ws.current.onclose = () => {
                console.log("WebSocket disconnected");
                setIsConnected(false);
            };

            // Cleanup on component unmount or if shouldConnect changes to false
            return () => {
                ws.current?.close();
            };
        } else {
            // If we shouldn't connect, ensure we are disconnected
            ws.current?.close();
            setIsConnected(false);
        }
    }, [token, onMessage, onError, shouldConnect, jobId]);
    // --- END UPDATED ---

    return { isConnected };
};