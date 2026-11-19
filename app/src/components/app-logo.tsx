import type { SVGProps } from "react"

import { cn } from "@/lib/utils"

import { BODY, SPARKS } from "./mascot"

/**
 * The Boomy mark on its tile: the mascot's round body and sparks, with two eyes. The
 * colours are the sidebar-primary tokens, which flip with the theme. Minimum size 16px.
 */
export function AppLogo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 120 120"
      aria-hidden
      className={cn("size-7 shrink-0", className)}
    >
      <rect width="120" height="120" rx="30" fill="var(--sidebar-primary)" />
      <g
        transform="translate(16.8 16.8) scale(0.72)"
        fill="var(--sidebar-primary-foreground)"
      >
        <path d={BODY} />
        {SPARKS.map(([cx, cy, r]) => (
          <circle key={cx} cx={cx} cy={cy} r={r} />
        ))}
        <circle cx="45" cy="64" r="8.5" fill="var(--sidebar-primary)" />
        <circle cx="71" cy="64" r="8.5" fill="var(--sidebar-primary)" />
      </g>
    </svg>
  )
}

/** The Boomy mark as a line icon in `currentColor`, beside lucide's in lists like Settings. */
export function MascotIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 120 120" aria-hidden {...props}>
      <path
        d={BODY}
        fill="none"
        stroke="currentColor"
        strokeWidth="10"
        strokeLinejoin="round"
      />
      {SPARKS.map(([cx, cy, r]) => (
        <circle key={cx} cx={cx} cy={cy} r={r} fill="currentColor" />
      ))}
      <circle cx="45" cy="64" r="8.5" fill="currentColor" />
      <circle cx="71" cy="64" r="8.5" fill="currentColor" />
    </svg>
  )
}
