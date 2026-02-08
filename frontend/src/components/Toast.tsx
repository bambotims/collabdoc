import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

type ToastVariant = "info" | "success" | "error";

type ToastItem = {
  id: number;
  message: string;
  variant: ToastVariant;
};

type PushToastOptions = {
  variant?: ToastVariant;
  durationMs?: number;
};

type ToastContextValue = {
  pushToast: (message: string, options?: PushToastOptions) => number;
  dismissToast: (toastId: number) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

type ToastProviderProps = {
  children: ReactNode;
};

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextIdRef = useRef(1);
  const timeoutByIdRef = useRef<Map<number, number>>(new Map());

  const dismissToast = useCallback((toastId: number) => {
    const timeoutId = timeoutByIdRef.current.get(toastId);
    if (timeoutId !== undefined) {
      window.clearTimeout(timeoutId);
      timeoutByIdRef.current.delete(toastId);
    }
    setToasts((previous) => previous.filter((toast) => toast.id !== toastId));
  }, []);

  const pushToast = useCallback(
    (message: string, options?: PushToastOptions) => {
      const id = nextIdRef.current++;
      const variant = options?.variant ?? "info";
      const durationMs = options?.durationMs ?? 3600;
      setToasts((previous) => [...previous, { id, message, variant }]);

      const timeoutId = window.setTimeout(() => {
        dismissToast(id);
      }, durationMs);
      timeoutByIdRef.current.set(id, timeoutId);
      return id;
    },
    [dismissToast]
  );

  useEffect(() => {
    return () => {
      timeoutByIdRef.current.forEach((timeoutId) => {
        window.clearTimeout(timeoutId);
      });
      timeoutByIdRef.current.clear();
    };
  }, []);

  const contextValue = useMemo(
    () => ({
      pushToast,
      dismissToast,
    }),
    [pushToast, dismissToast]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

type ToastViewportProps = {
  toasts: ToastItem[];
  onDismiss: (toastId: number) => void;
};

function ToastViewport({ toasts, onDismiss }: ToastViewportProps) {
  return (
    <div className="toast-viewport" aria-live="polite" aria-atomic="true">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast-${toast.variant}`}>
          <p>{toast.message}</p>
          <button className="toast-close" onClick={() => onDismiss(toast.id)} aria-label="Dismiss notification">
            x
          </button>
        </div>
      ))}
    </div>
  );
}
