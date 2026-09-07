/**
 * Centralized Application Configuration Module for Frontend
 * Reads import.meta.env strictly once at startup, validates required keys,
 * and exports a frozen, typed config object.
 */

function requireEnvVar(key: string, value: string | undefined): string {
  if (!value || value.trim() === '') {
    throw new Error(`[Config Error] Missing required environment variable: ${key}`);
  }
  return value.trim();
}

const rawApiUrl = requireEnvVar('VITE_API_URL', import.meta.env.VITE_API_URL);
const trimmedApiUrl = rawApiUrl.replace(/\/+$/, '');

export const config = Object.freeze({
  apiUrl: trimmedApiUrl,
  apiBaseUrl: trimmedApiUrl.endsWith('/api') ? trimmedApiUrl : `${trimmedApiUrl}/api`,
  supabaseUrl: requireEnvVar('VITE_SUPABASE_URL', import.meta.env.VITE_SUPABASE_URL),
  supabaseAnonKey: requireEnvVar('VITE_SUPABASE_ANON_KEY', import.meta.env.VITE_SUPABASE_ANON_KEY),
});

export default config;
