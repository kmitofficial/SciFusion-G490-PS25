// Location: frontend/context/AuthContext.tsx
"use client";

import React, {
    createContext,
    useState,
    useEffect,
    useCallback,
    ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { jwtDecode } from "jwt-decode";

interface User {
    id: string;
    username: string;
    email: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (formData: URLSearchParams) => Promise<void>;
    logout: () => void;
    signup: (userData: any) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const isTokenValid = (token: string): boolean => {
    try {
        const decoded: { exp: number } = jwtDecode(token);
        const now = Date.now() / 1000;
        return decoded.exp > now;
    } catch (e) {
        return false;
    }
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();

    const loadUserFromToken = useCallback(async (token: string) => {
        if (isTokenValid(token)) {
            try {
                const currentUser = await api.get("/auth/me", token);
                setUser(currentUser);
                setToken(token);
            } catch (e) {
                console.error("Failed to fetch user with token", e);
                localStorage.removeItem("token");
                setToken(null);
                setUser(null);
            }
        } else {
            localStorage.removeItem("token");
            setToken(null);
            setUser(null);
        }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        const storedToken = localStorage.getItem("token");
        if (storedToken) {
            loadUserFromToken(storedToken);
        } else {
            setIsLoading(false);
        }
    }, [loadUserFromToken]);

    const login = async (formData: URLSearchParams) => {
        try {
            // FastAPI's OAuth2PasswordRequestForm expects x-www-form-urlencoded
            const response = await fetch("http://localhost:8000/api/v1/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new ApiError(data.detail || "Login failed", response.status, data);
            }

            const { access_token } = data;
            localStorage.setItem("token", access_token);
            await loadUserFromToken(access_token);
            router.push("/app/dashboard");
        } catch (error) {
            console.error("Login failed", error);
            throw error; // Re-throw to be caught by the form
        }
    };

    const signup = async (userData: any) => {
        try {
            await api.post("/auth/signup", userData);
            // On success, redirect to login
            router.push("/login");
        } catch (error) {
            console.error("Signup failed", error);
            throw error; // Re-throw to be caught by the form
        }
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem("token");
        router.push("/login");
    };

    return (
        <AuthContext.Provider
            value={{
        user,
            token,
            isAuthenticated: !!user,
            isLoading,
            login,
            logout,
            signup,
    }}
>
    {children}
    </AuthContext.Provider>
);
};

export default AuthContext;