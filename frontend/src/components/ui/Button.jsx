import { forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "./Card";

export const Button = forwardRef(
  ({ className, variant = "primary", size = "default", loading = false, disabled, children, ...props }, ref) => {
    
    const baseClass = "inline-flex items-center justify-center rounded-xl font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:pointer-events-none disabled:opacity-50 hover:shadow-lg hover:shadow-indigo-500/30";
    
    const variants = {
      primary: "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-lg shadow-indigo-500/40 hover:from-indigo-700 hover:to-indigo-600 hover:shadow-indigo-500/60",
      secondary: "bg-slate-800 text-slate-100 border border-slate-700 shadow-md shadow-black/50 hover:bg-slate-700 hover:border-slate-600",
      ghost: "text-slate-300 hover:bg-slate-800/50 hover:text-white",
      outline: "border-2 border-indigo-500 text-indigo-400 hover:bg-indigo-500/10",
      danger: "bg-gradient-to-r from-red-600 to-red-500 text-white shadow-lg shadow-red-500/40 hover:from-red-700 hover:to-red-600"
    };

    const sizes = {
      default: "h-11 px-6 py-2",
      sm: "h-9 px-4 text-sm",
      lg: "h-14 px-8 text-lg rounded-2xl",
      icon: "h-10 w-10 p-2"
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(baseClass, variants[variant], sizes[size], className)}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";