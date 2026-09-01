import { OfficeSidebar } from '@/components/office/OfficeSidebar';
import { OfficeTopBar } from '@/components/office/OfficeTopBar';

export default function OfficeLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0c12]">
      <OfficeSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <OfficeTopBar />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
