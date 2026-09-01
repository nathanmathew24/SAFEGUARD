import { OfficeSidebar } from "./OfficeSidebar";
import { OfficeTopBar } from "./OfficeTopBar";

export function OfficeShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <OfficeSidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <OfficeTopBar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
