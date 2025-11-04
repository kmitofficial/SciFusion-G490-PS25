// Location: frontend/hooks/useWebSocket.ts
"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "./useAuth";

const getWebSocketUrl = () => {
    // Default to localhost, but allow override via environment variable
    const wsUrl =
        process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws";
    return wsUrl;
};

export const useWebSocket = (
    onMessage: (message: any) => void,
    onError: (error: string) => void,
) => {
    const { token } = useAuth();
    const ws = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        if (token) {
            const wsUrl = `${getWebSocketUrl()}?token=${token}`;
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
                    // Handle non-JSON or plain text log messages
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

            // Cleanup on component unmount
            return () => {
                ws.current?.close();
            };
        }
    }, [token, onMessage, onError]);

    return { isConnected };
};