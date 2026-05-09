import type { ReactNode } from "react";
import IKSBadge from "./IKSBadge";

export interface CopilotShellTab {
  id: string;
  label: string;
}

export interface CopilotShellProps {
  name: string;
  icon: string;
  tabs: CopilotShellTab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  iks: number;
  iksDelta?: number;
  children: ReactNode;
}

export default function CopilotShell({
  name,
  icon,
  tabs,
  activeTab,
  onTabChange,
  iks,
  iksDelta,
  children,
}: CopilotShellProps) {
  return (
    <div
      className="min-h-screen px-8 py-6"
      style={{
        background: "var(--copilot-bg)",
        color: "var(--copilot-text)",
        fontFamily: "var(--copilot-font-sans)",
      }}
    >
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="copilot-card flex items-center justify-between px-6 py-5">
          <div className="flex min-w-0 items-center gap-4">
            <div
              className="grid h-12 w-12 place-items-center rounded-md text-2xl"
              style={{
                background: "var(--copilot-surface-muted)",
                color: "var(--copilot-primary)",
              }}
              aria-hidden="true"
            >
              {icon}
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-xl font-semibold">{name}</h1>
              <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
                Compounding intelligence workspace
              </p>
            </div>
          </div>
          <IKSBadge value={iks} delta={iksDelta} size="sm" />
        </header>

        <nav className="flex gap-2 border-b pb-2" style={{ borderColor: "var(--copilot-border)" }}>
          {tabs.map((tab) => {
            const selected = tab.id === activeTab;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onTabChange(tab.id)}
                className="rounded-md px-4 py-2 text-sm font-semibold transition"
                style={{
                  background: selected ? "var(--copilot-primary)" : "transparent",
                  color: selected ? "var(--copilot-primary-contrast)" : "var(--copilot-text-muted)",
                }}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>

        <main className="min-h-[32rem]">{children}</main>
      </div>
    </div>
  );
}
