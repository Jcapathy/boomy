import { cn } from "@/lib/utils"

/** The `boomy` wordmark: always lowercase, in the heading font, bold. */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "font-heading text-base leading-5 font-bold tracking-[-0.02em]",
        className
      )}
    >
      boomy
    </span>
  )
}
