import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

// Server Supabase client — use this in Server Components, Route Handlers, and middleware.
// Must be called inside a Request context (i.e., inside a component render or handler).
export async function createSupabaseServerClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // setAll called from a Server Component — cookies can't be set.
            // Middleware handles the refresh, so this is safe to ignore.
          }
        },
      },
    },
  );
}
