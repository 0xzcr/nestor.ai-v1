import * as React from "react";

import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "ghost";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-full px-5 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-sky-400/60 disabled:cursor-not-allowed disabled:opacity-60",
        variant === "default" &&
          "bg-[linear-gradient(135deg,#2563eb,#22d3ee)] text-slate-950 hover:brightness-110",
        variant === "secondary" &&
          "border border-white/10 bg-white/10 text-white hover:bg-white/15",
        variant === "ghost" && "text-slate-300 hover:bg-white/5",
        className
      )}
      {...props}
    />
  )
);

Button.displayName = "Button";
