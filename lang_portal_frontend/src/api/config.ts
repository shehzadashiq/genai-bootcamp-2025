import axios from 'axios';

// Custom error interface for API errors
interface APIError extends Error {
  status?: number;
  data?: any;
}

// Create axios instance with custom config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8080/api',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor for logging and validation
api.interceptors.request.use(
  (config) => {
    // Log request details
    console.log(`API Request [${config.method?.toUpperCase()}] ${config.url}`, {
      data: config.data,
      params: config.params,
      headers: config.headers,
    });

    // Validate request data for specific endpoints
    if (config.url?.includes('/listening/download-transcript') || config.url?.includes('/listening/questions')) {
      const { url } = config.data || {};
      if (!url?.trim()) {
        const error = new Error('Video URL or ID is required') as APIError;
        error.status = 400;
        throw error;
      }
    }

    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    // Log successful response
    console.log(`API Response [${response.status}] ${response.config.url}`, {
      data: response.data,
      headers: response.headers,
    });
    return response;
  },
  (error) => {
    // Log error details
    if (error.response) {
      // Server responded with error
      console.error('API Error Response:', {
        status: error.response.status,
        data: error.response.data,
        headers: error.response.headers,
        url: error.config?.url,
        method: error.config?.method,
      });
    } else if (error.request) {
      // Request made but no response
      console.error('API Request Failed:', {
        request: error.request,
        url: error.config?.url,
        method: error.config?.method,
      });
    } else {
      // Error in request configuration
      console.error('API Error:', {
        message: error.message,
        url: error.config?.url,
        method: error.config?.method,
      });
    }

    // Enhance error object with additional context
    const enhancedError = new Error(
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    ) as APIError;
    
    enhancedError.name = 'APIError';
    enhancedError.status = error.response?.status;
    enhancedError.data = error.response?.data;

    return Promise.reject(enhancedError);
  }
);

export default api;
