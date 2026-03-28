import { clsx } from "clsx";  
import { twMerge } from "tailwind-merge";  
  
export function cn(...inputs) {  
  return twMerge(clsx(inputs));  
}  
  
export function Card({ className, ...props }) {  
  return (  
    <div  
      className={cn("rounded-2xl border border-slate-800 bg-slate-900/50 shadow-xl shadow-black/50 overflow-hidden backdrop-blur-sm hover:border-slate-700 transition-all duration-300 hover:shadow-indigo-500/20", className)}  
      {...props}  
    />  
  );  
}  
  
export function CardHeader({ className, ...props }) {  
  return <div className={cn("px-6 py-5 border-b border-slate-800/50", className)} {...props} />;  
}  
  
export function CardTitle({ className, ...props }) {  
  return <h3 className={cn("text-xl font-bold leading-none tracking-tight text-white", className)} {...props} />;  
}  
  
export function CardDescription({ className, ...props }) {  
  return <p className={cn("mt-2 text-sm text-slate-400", className)} {...props} />;  
}  
  
export function CardContent({ className, ...props }) {  
  return <div className={cn("p-6", className)} {...props} />;  
}  
  
export function CardFooter({ className, ...props }) {  
  return <div className={cn("px-6 py-4 flex items-center border-t border-slate-800/50 bg-slate-950/50", className)} {...props} />;  
}  
