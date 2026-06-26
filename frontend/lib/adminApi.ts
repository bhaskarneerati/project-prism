import axios from "axios";

export const adminApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

adminApi.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("admin_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

adminApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("admin_token");
      window.location.href = "/admin/login";
    }
    return Promise.reject(error);
  }
);
