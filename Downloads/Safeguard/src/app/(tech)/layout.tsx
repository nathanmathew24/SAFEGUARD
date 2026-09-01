import { TechShell } from "@/components/tech/TechShell";

export default function TechLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <TechShell>{children}</TechShell>;
}
