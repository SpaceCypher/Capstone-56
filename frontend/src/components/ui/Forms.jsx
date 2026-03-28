import { forwardRef } from "react";
import { cn } from "./Card";

export const Input = forwardRef(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-12 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-white shadow-md shadow-black/50 transition-all placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 file:border-0 file:bg-transparent file:text-sm file:font-medium hover:border-slate-600",
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Input.displayName = "Input";

export const Textarea = forwardRef(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        "flex min-h-[120px] w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white shadow-md shadow-black/50 transition-all placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:border-indigo-500 disabled:cursor-not-allowed disabled:opacity-50 hover:border-slate-600",
        className
      )}
      ref={ref}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";

export function Label({ className, children, ...props }) {
  return (
    <label
      className={cn(
        "text-sm font-semibold leading-none text-slate-300 peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        className
      )}
      {...props}
    >
      {children}
    </label>
  );
}

export function Badge({ className, variant = "default", children, ...props }) {
  const variants = {
    default: "bg-slate-800 text-slate-300 border-slate-700",
    primary: "bg-indigo-900/50 text-indigo-300 border-indigo-700",
    success: "bg-emerald-900/50 text-emerald-300 border-emerald-700",
    warning: "bg-amber-900/50 text-amber-300 border-amber-700",
    danger: "bg-rose-900/50 text-rose-300 border-rose-700",
    outline: "bg-transparent text-slate-400 border-slate-700"
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-950",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
