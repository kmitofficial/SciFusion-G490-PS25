// Location: frontend/lib/api.ts
export class ApiError extends Error {
    status: number;
    data: any;

    constructor(message: string, status: number, data: any) {
        super(message);
        this.name = "ApiError";
        this.status = status;
        this.data = data;
    }
}

const getApiUrl = () => {
    // Use environment variable if set, otherwise default
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
};

export const api = {
    async get(endpoint: string, token?: string) {
        return this.request("GET", endpoint, null, token);
    },

    async post(endpoint: string, body: any, token?: string) {
        return this.request("POST", endpoint, body, token);
    },

    // Add other methods (put, delete) as needed

    async request(
        method: string,
        endpoint: string,
        body: any = null,
        token?: string,
    ) {
        const headers = new Headers();
        if (body && !(body instanceof FormData)) {
            headers.set("Content-Type", "application/json");
        }
        if (token) {
            headers.set("Authorization", `Bearer ${token}`);
        }

        const config: RequestInit = {
            method,
            headers,
        };

        if (body) {
            config.body = (body instanceof FormData) ? body : JSON.stringify(body);
        }

        const url = `${getApiUrl()}${endpoint}`;

        try {
            const response = await fetch(url, config);
            const data = await response.json().catch(() => ({})); // Handle empty responses

            if (!response.ok) {
                const errorMessage = data.detail || `HTTP error! status: ${response.status}`;
                throw new ApiError(errorMessage, response.status, data);
            }

            return data;
        } catch (error) {
            console.error("API request failed:", error);
            if (error instanceof ApiError) {
                throw error; // Re-throw known API errors
            }
            // Throw a generic error for network failures, etc.
            throw new ApiError("A network error occurred.", 500, null);
        }
    },
};