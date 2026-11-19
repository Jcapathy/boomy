import { X } from "lucide-react"
import { AnimatePresence, motion } from "motion/react"

import { MascotCard } from "@/components/mascot-card"
import { Button } from "@/components/ui/button"
import { createStore, useStore } from "@/lib/store"

/** Whether the agent set `attribute` to say part of the call isn't available
 * (agent/memory.py, agent/agent.py). */
export function unavailable(
  attributes: Record<string, string>,
  attribute: string
): boolean {
  return attributes[attribute] === "unavailable"
}

// For each card, the call (its `startedAt`) whose card the user closed; outlives the call
// view, which unmounts while the user looks at another project.
const closedFor = createStore<Record<string, number>>({})

/**
 * The card a call shows when part of Boomy isn't available: the failed mascot, and the call
 * going on as usual. Once closed, it stays closed for the rest of the call.
 */
export function UnavailableCard({
  id,
  call,
  shown,
  headline,
  detail,
  className,
}: {
  /** Which card, so closing one leaves the others. */
  id: string
  /** The call's `startedAt`. */
  call: number
  shown: boolean
  headline: string
  detail: string
  className?: string
}) {
  const closed = useStore(closedFor)[id] === call

  return (
    <AnimatePresence>
      {shown && !closed && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className={className}
        >
          <MascotCard
            state="failed"
            headline={headline}
            detail={detail}
            announce="status"
            action={
              <Button
                variant="ghost"
                size="icon-sm"
                aria-label="Close"
                onClick={() =>
                  closedFor.set({ ...closedFor.get(), [id]: call })
                }
              >
                <X />
              </Button>
            }
          />
        </motion.div>
      )}
    </AnimatePresence>
  )
}
