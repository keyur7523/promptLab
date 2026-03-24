/**
 * Shared API configuration.
 *
 * API key is read at runtime from localStorage (set after key rotation)
 * with fallback to the build-time VITE_API_KEY env var.
 */

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const STORAGE_KEY = 'promptlab_api_key';

export function getApiKey(): string {
  return localStorage.getItem(STORAGE_KEY) || import.meta.env.VITE_API_KEY || '';
}

export function setApiKey(key: string): void {
  localStorage.setItem(STORAGE_KEY, key);
}

export function apiHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'x-api-key': getApiKey(),
  };
}
