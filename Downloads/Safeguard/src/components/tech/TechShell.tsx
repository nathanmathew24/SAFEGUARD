import { TechBottomNav } from "./TechBottomNav";

export function TechShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen max-w-md mx-auto relative pb-20">
      <main className="min-h-screen">{children}</main>
      <TechBottomNav />
    </div>
  );
}
