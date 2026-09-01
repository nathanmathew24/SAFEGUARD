// shadcn: Card, Badge, Progress, Table, Avatar
"use client";

import Link from "next/link";
import { AlertTriangle, CheckCircle2, Clock, TrendingUp } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  GlassCard,
  GlassCardHeader,
  GlassCardContent,
  GlassCardTitle,
} from "@/components/shared/GlassCard";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { TradeBadge } from "@/components/shared/TradeBadge";
import { HealthIndicator } from "@/components/shared/HealthIndicator";
import { mockData } from "@/lib/mockData";
import { formatDate, getStatusColor } from "@/lib/utils";

const { buildings, visits, issues } = mockData;

// Compute KPIs
const openIssues = issues.filter((i) => i.status !== "resolved").length;
const thisWeekVisits = visits.filter((v) => {
  const d = new Date(v.scheduledDate);
  const now = new Date("2026-09-01");
  const start = new Date(now);
  start.setDate(now.getDate() - now.getDay());
  const end = new Date(start);
  end.setDate(start.getDate() + 7);
  return d >= start && d < end;
}).length;
const portfolioHealth = Math.round(
  (buildings.filter((b) => b.health === "ok").length / buildings.length) * 100
);

// Decision items
const decisionItems = [
  ...visits
    .filter((v) => v.status === "overdue")
    .map((v) => {
      const b = buildings.find((b) => b.id === v.buildingId);
      return {
        id: v.id,
        label: `Overdue inspection — ${b?.name}`,
        trade: v.trade,
        status: "critical" as const,
        href: "/schedule",
        action: "View Schedule",
      };
    }),
  ...issues
    .filter((i) => i.priority === "high" && i.status === "open")
    .map((i) => {
      const b = buildings.find((b) => b.id === i.buildingId);
      return {
        id: i.id,
        label: i.description.slice(0, 60) + "…",
        trade: i.trade,
        status: "critical" as const,
        href: "/issues",
        action: "View Issue",
      };
    }),
];

// Live event feed
const events = [
  {
    id: "e1",
    time: "09:45",
    text: "EX-014 failed pressure check",
    building: "Al Quoz Industrial",
    trade: "fire" as const,
    status: "critical" as const,
  },
  {
    id: "e2",
    time: "10:10",
    text: "EX-015 inspection passed",
    building: "Al Quoz Industrial",
    trade: "fire" as const,
    status: "ok" as const,
  },
  {
    id: "e3",
    time: "11:30",
    text: "Visit v1 completed",
    building: "Al Quoz Industrial",
    trade: "fire" as const,
    status: "ok" as const,
  },
  {
    id: "e4",
    time: "13:00",
    text: "AHU-07 inspection passed",
    building: "Al Reem Tower",
    trade: "hvac" as const,
    status: "ok" as const,
  },
  {
    id: "e5",
    time: "14:00",
    text: "HD-03 certificate overdue",
    building: "Sharjah Expo Center",
    trade: "fire" as const,
    status: "warning" as const,
  },
];

export default function OverviewPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text-primary)]">
          Overview
        </h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-0.5">
          Emirates Safety Systems — Mon 1 Sep 2026
        </p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard className="p-5">
          <GlassCardTitle>Portfolio Health</GlassCardTitle>
          <div className="mt-3">
            <div className="text-3xl font-bold text-[var(--color-text-primary)] mb-2">
              {portfolioHealth}%
            </div>
            <Progress
              value={portfolioHealth}
              className="h-1.5 bg-white/10"
            />
            <p className="text-xs text-[var(--color-text-muted)] mt-1.5">
              {buildings.filter((b) => b.health === "ok").length} of{" "}
              {buildings.length} buildings OK
            </p>
          </div>
        </GlassCard>

        <GlassCard className="p-5">
          <GlassCardTitle>Buildings</GlassCardTitle>
          <div className="mt-3 flex items-end gap-2">
            <span className="text-3xl font-bold text-[var(--color-text-primary)]">
              {buildings.length}
            </span>
            <span className="text-xs text-[var(--color-text-muted)] mb-1">
              monitored
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Dubai · Sharjah · Abu Dhabi
          </p>
        </GlassCard>

        <GlassCard className="p-5">
          <GlassCardTitle>Inspections This Week</GlassCardTitle>
          <div className="mt-3 flex items-end gap-2">
            <span className="text-3xl font-bold text-[var(--color-text-primary)]">
              {thisWeekVisits}
            </span>
            <span className="text-xs text-[var(--color-text-muted)] mb-1">
              visits
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            {visits.filter((v) => v.status === "completed").length} completed
          </p>
        </GlassCard>

        <GlassCard className="p-5">
          <GlassCardTitle>Open Issues</GlassCardTitle>
          <div className="mt-3 flex items-end gap-2">
            <span
              className={`text-3xl font-bold ${
                openIssues > 2
                  ? "text-[var(--color-status-critical)]"
                  : "text-[var(--color-status-warning)]"
              }`}
            >
              {openIssues}
            </span>
            <span className="text-xs text-[var(--color-text-muted)] mb-1">
              issues
            </span>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            {issues.filter((i) => i.priority === "high").length} high priority
          </p>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Requires a Decision */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Requires a Decision</GlassCardTitle>
            </GlassCardHeader>
            <GlassCardContent className="pt-0">
              <div className="flex flex-col gap-2">
                {decisionItems.length === 0 && (
                  <p className="text-sm text-[var(--color-text-muted)] py-4 text-center">
                    No pending decisions
                  </p>
                )}
                {decisionItems.map((item) => {
                  const colors = getStatusColor(item.status);
                  return (
                    <div
                      key={item.id}
                      className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]"
                    >
                      <AlertTriangle
                        className={`w-4 h-4 flex-shrink-0 ${colors.text}`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-[var(--color-text-primary)] truncate">
                          {item.label}
                        </p>
                        <TradeBadge trade={item.trade} className="mt-1" />
                      </div>
                      <Link href={item.href}>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-xs h-7 text-[var(--color-accent-primary)] hover:text-[var(--color-accent-primary)] hover:bg-[var(--color-accent-glow)]"
                        >
                          {item.action}
                        </Button>
                      </Link>
                    </div>
                  );
                })}
              </div>
            </GlassCardContent>
          </GlassCard>

          {/* Building Health Grid */}
          <GlassCard>
            <GlassCardHeader>
              <GlassCardTitle>Building Health</GlassCardTitle>
            </GlassCardHeader>
            <GlassCardContent className="pt-0">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {buildings.map((b) => (
                  <Link key={b.id} href={`/buildings/${b.id}`}>
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-white/[0.1] transition-colors">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <p className="text-sm font-medium text-[var(--color-text-primary)] leading-tight">
                            {b.name}
                          </p>
                          <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                            {b.emirate}
                          </p>
                        </div>
                        <StatusBadge status={b.health} />
                      </div>
                      <div className="flex gap-2 flex-wrap">
                        {b.trades.map((trade) => {
                          const th = b.tradeHealth[trade];
                          return (
                            <div
                              key={trade}
                              className="flex items-center gap-1.5"
                            >
                              <TradeBadge trade={trade} />
                              {th && <HealthIndicator status={th} showLabel={false} size="sm" />}
                            </div>
                          );
                        })}
                      </div>
                      <p className="text-xs text-[var(--color-text-subtle)] mt-2">
                        Next: {formatDate(b.nextInspection)}
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            </GlassCardContent>
          </GlassCard>
        </div>

        {/* Live Event Feed */}
        <GlassCard className="flex flex-col">
          <GlassCardHeader>
            <GlassCardTitle>Live Event Feed</GlassCardTitle>
          </GlassCardHeader>
          <GlassCardContent className="flex-1 pt-0">
            <div className="flex flex-col gap-2">
              {events.map((ev) => {
                const colors = getStatusColor(ev.status);
                return (
                  <div
                    key={ev.id}
                    className="flex gap-3 p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04]"
                  >
                    <div
                      className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${colors.dot}`}
                    />
                    <div className="min-w-0">
                      <p className="text-xs text-[var(--color-text-primary)] leading-snug">
                        {ev.text}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span className="text-[10px] text-[var(--color-text-muted)]">
                          {ev.building}
                        </span>
                        <span className="text-[10px] text-[var(--color-text-subtle)]">
                          ·
                        </span>
                        <TradeBadge trade={ev.trade} className="text-[10px] py-0 px-1.5" />
                      </div>
                      <p className="text-[10px] text-[var(--color-text-subtle)] mt-0.5">
                        Today {ev.time}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </GlassCardContent>
        </GlassCard>
      </div>
    </div>
  );
}
