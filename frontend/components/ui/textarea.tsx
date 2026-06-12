import * as React from "react";

import { cn } from "@/lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "min-h-28 w-full resize-none border-0 bg-transparent text-sm leading-7 text-white outline-none placeholder:text-slate-500",
      className
    )}
    {...props}
  />
));

Textarea.displayName = "Textarea";
