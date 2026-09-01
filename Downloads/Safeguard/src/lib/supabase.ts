import { createBrowserClient } from '@supabase/ssr';

// Browser Supabase client — use this in 'use client' components.
export function createSupabaseClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
  );
}
