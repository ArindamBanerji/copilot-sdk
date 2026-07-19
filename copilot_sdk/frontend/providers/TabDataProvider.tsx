import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { TRADING_INDIVIDUAL_ENDPOINTS } from "./tradingEndpointMap";

type TabDataStatus = "ready" | "refreshing" | "missing" | "invalidated_error" | "dynamic" | "unknown_key";

export interface TabDataEnvelope<T = unknown> {
  data: T | null;
  previousData?: T | null;
  error: string | null;
  status: TabDataStatus | string;
}

interface TabDataContextValue {
  copilot: string;
  entries: Record<string, TabDataEnvelope>;
  refreshKey: (key: string) => Promise<void>;
}

export interface TabDataProviderProps {
  copilot: string;
  // Copilot screens pass narrowed manifest arrays such as readonly TradingKey[].
  // This shared provider keeps the cross-copilot boundary as readonly string[].
  keys: readonly string[];
  children: React.ReactNode;
}

export interface UseTabDataResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  status: string;
  refreshing: boolean;
  refresh: () => void;
}

export interface UseDerivedDataResult<D> {
  data: D | null;
  loading: boolean;
  error: string | null;
  refreshing: boolean;
}

const DEFAULT_API_BASE = "http://127.0.0.1:8010";
const TabDataContext = createContext<TabDataContextValue | null>(null);

// C-E: This provider NEVER emits console.error.
// All recoverable states use console.debug.
function apiBase(): string {
  const meta = import.meta as ImportMeta & { env?: { VITE_API_URL?: string } };
  return meta.env?.VITE_API_URL || DEFAULT_API_BASE;
}

function toCamelKey(key: string): string {
  return key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
}

function normalizeKeys<T = unknown>(value: unknown): T {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeKeys(item)) as T;
  }
  if (value && typeof value === "object") {
    const output: Record<string, unknown> = {};
    for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
      output[toCamelKey(key)] = normalizeKeys(nested);
    }
    return output as T;
  }
  return value as T;
}

function missingEnvelope(): TabDataEnvelope {
  return { data: null, error: null, status: "missing" };
}

function normalizeEnvelope(value: unknown): TabDataEnvelope {
  const envelope = normalizeKeys<TabDataEnvelope>(value);
  const status = envelope.status || "missing";
  const data = status === "refreshing" && envelope.previousData !== undefined
    ? envelope.previousData
    : envelope.data;
  return {
    data: data ?? null,
    previousData: envelope.previousData ?? null,
    error: envelope.error ?? null,
    status,
  };
}

function uniqueKeys(keys: readonly string[]): string[] {
  return Array.from(new Set(keys.filter(Boolean)));
}

function individualEndpoint(copilot: string, key: string): string | null {
  if (copilot !== "trading") {
    return null;
  }
  return TRADING_INDIVIDUAL_ENDPOINTS[key] || null;
}

async function fetchTabState(copilot: string, keys: string[]): Promise<Record<string, TabDataEnvelope>> {
  const requestKeys = uniqueKeys(keys);
  if (requestKeys.length === 0) {
    return {};
  }
  const params = new URLSearchParams({ keys: requestKeys.join(",") });
  const response = await fetch(`${apiBase()}/api/${encodeURIComponent(copilot)}/tab-state?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`GET /api/${copilot}/tab-state failed with ${response.status}`);
  }
  const payload = (await response.json()) as Record<string, unknown>;
  return Object.fromEntries(Object.entries(payload).map(([key, value]) => [key, normalizeEnvelope(value)]));
}

async function fetchIndividual(copilot: string, key: string): Promise<TabDataEnvelope | null> {
  const endpoint = individualEndpoint(copilot, key);
  if (!endpoint) {
    return null;
  }
  const response = await fetch(`${apiBase()}${endpoint}`);
  if (!response.ok) {
    throw new Error(`GET ${endpoint} failed with ${response.status}`);
  }
  return { data: normalizeKeys(await response.json()), error: null, status: "ready" };
}

export function TabDataProvider({ copilot, keys, children }: TabDataProviderProps) {
  const stableKeySignature = JSON.stringify(keys);
  const stableKeys = useMemo(
    () => keys,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [stableKeySignature],
  );
  const requestKeys = useMemo(() => uniqueKeys(stableKeys), [stableKeys]);
  const [entries, setEntries] = useState<Record<string, TabDataEnvelope>>(() =>
    Object.fromEntries(requestKeys.map((key) => [key, missingEnvelope()])),
  );

  useEffect(() => {
    let cancelled = false;
    setEntries((current) => ({
      ...Object.fromEntries(requestKeys.map((key) => [key, current[key] || missingEnvelope()])),
    }));

    fetchTabState(copilot, requestKeys)
      .then((payload) => {
        if (!cancelled) {
          setEntries((current) => ({ ...current, ...payload }));
        }
      })
      .catch((error) => {
        console.debug("tab-state fetch failed", error);
        if (!cancelled) {
          const message = error instanceof Error ? error.message : "Tab state unavailable";
          setEntries((current) => ({
            ...current,
            ...Object.fromEntries(
              requestKeys.map((key) => [key, { data: null, error: message, status: "invalidated_error" }]),
            ),
          }));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [copilot, requestKeys]);

  const refreshKey = useCallback(
    async (key: string) => {
      try {
        const individual = await fetchIndividual(copilot, key);
        if (individual) {
          setEntries((current) => ({ ...current, [key]: individual }));
        } else {
          const payload = await fetchTabState(copilot, [key]);
          setEntries((current) => ({ ...current, ...payload }));
        }
      } catch (error) {
        console.debug("tab-state refresh failed", error);
        const message = error instanceof Error ? error.message : "Tab state refresh failed";
        setEntries((current) => ({
          ...current,
          [key]: {
            data: null,
            previousData: current[key]?.data ?? null,
            error: message,
            status: "invalidated_error",
          },
        }));
      }
    },
    [copilot],
  );

  const value = useMemo<TabDataContextValue>(() => ({ copilot, entries, refreshKey }), [copilot, entries, refreshKey]);

  return <TabDataContext.Provider value={value}>{children}</TabDataContext.Provider>;
}

export function useTabData<T>(key: string): UseTabDataResult<T> {
  const context = useContext(TabDataContext);
  const envelope = context?.entries[key] || missingEnvelope();
  const status = envelope.status || "missing";

  return {
    data: (envelope.data as T | null) ?? null,
    loading: status === "missing",
    error: envelope.error,
    status,
    refreshing: status === "refreshing",
    refresh: () => {
      void context?.refreshKey(key);
    },
  };
}

export function useDerivedData<S, D>(sourceKey: string, transform: (source: S) => D): UseDerivedDataResult<D> {
  const source = useTabData<S>(sourceKey);
  const data = useMemo(() => {
    if (source.data === null) {
      return null;
    }
    return transform(source.data);
  }, [source.data, transform]);

  return {
    data,
    loading: source.loading,
    error: source.error,
    refreshing: source.refreshing,
  };
}
