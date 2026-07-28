type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  details?: unknown;
  requestId?: string;
  duration?: number;
}

function formatLog(entry: LogEntry): string {
  return JSON.stringify(entry);
}

function log(level: LogLevel, message: string, details?: unknown) {
  const entry: LogEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...(details ? { details } : {}),
  };

  const formatted = formatLog(entry);

  switch (level) {
    case "error":
      console.error(formatted);
      break;
    case "warn":
      console.warn(formatted);
      break;
    case "debug":
      if (process.env.NODE_ENV !== "production") console.debug(formatted);
      break;
    default:
      console.log(formatted);
  }
}

export const logger = {
  debug: (message: string, details?: unknown) => log("debug", message, details),
  info: (message: string, details?: unknown) => log("info", message, details),
  warn: (message: string, details?: unknown) => log("warn", message, details),
  error: (message: string, error?: Error, details?: unknown) => {
    log("error", message, {
      ...(details ? { details } : {}),
      ...(error ? { error: error.message, stack: error.stack } : {}),
    });
  },
  api: (method: string, path: string, status: number, duration: number) => {
    log("info", `${method} ${path} ${status}`, { method, path, status, duration });
  },
};
