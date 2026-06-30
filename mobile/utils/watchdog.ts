import { AppState, type AppStateStatus } from 'react-native';

type WatchdogEvent = {
  ts: string;
  event: string;
  data?: Record<string, unknown>;
};

const MAX_EVENTS = 60;
const events: WatchdogEvent[] = [];

export function logWatchdog(event: string, data?: Record<string, unknown>) {
  const entry: WatchdogEvent = {
    ts: new Date().toISOString(),
    event,
    data,
  };
  events.push(entry);
  if (events.length > MAX_EVENTS) {
    events.shift();
  }
}

function dumpRecentEvents() {
  // Silent watchdog events dump
}

export function startWatchdog(): () => void {
  logWatchdog('watchdog_start');

  const heartbeatId = setInterval(() => {
    logWatchdog('heartbeat');
  }, 10000);

  const handleAppStateChange = (state: AppStateStatus) => {
    logWatchdog('app_state', { state });
  };

  const subscription = AppState.addEventListener('change', handleAppStateChange);

  const handler = (error: unknown, isFatal?: boolean) => {
    logWatchdog('global_error', {
      isFatal: Boolean(isFatal),
      message: error instanceof Error ? error.message : String(error),
    });
    dumpRecentEvents();
    const originalHandler = (globalThis as typeof globalThis & { __watchdogOriginalHandler?: typeof ErrorUtils.setGlobalHandler }).__watchdogOriginalHandler;
    if (originalHandler) {
      try {
        originalHandler(error, isFatal ?? false);
      } catch {
        // no-op
      }
    }
  };

  if (globalThis.ErrorUtils?.setGlobalHandler) {
    const globalWithHandler = globalThis as typeof globalThis & { __watchdogOriginalHandler?: typeof ErrorUtils.setGlobalHandler };
    if (!globalWithHandler.__watchdogOriginalHandler) {
      globalWithHandler.__watchdogOriginalHandler = globalThis.ErrorUtils.getGlobalHandler?.() ?? undefined;
    }
    globalThis.ErrorUtils.setGlobalHandler(handler);
  }

  return () => {
    clearInterval(heartbeatId);
    subscription.remove();
  };
}
