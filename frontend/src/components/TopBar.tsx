"use client";

import { Show, UserButton, useClerk } from "@clerk/nextjs";
import Link from "next/link";
import Mascot from "./Mascot";

export default function TopBar({ trailing }: { trailing?: React.ReactNode }) {
  const { openSignIn } = useClerk();

  return (
    <header className="flex items-center justify-between px-5 py-4 sm:px-8">
      <Link href="/" className="flex items-center gap-2" aria-label="Mika">
        <Mascot size={26} />
        <span className="font-display text-lg tracking-tight">Mika</span>
      </Link>

      <div className="flex items-center gap-3">
        {trailing}
        <Show when="signed-out">
          <button
            onClick={() => openSignIn()}
            className="rounded-full border border-line px-4 py-1.5 text-sm text-muted transition-colors hover:border-line-strong hover:text-ink"
          >
            Anmelden
          </button>
        </Show>
        <Show when="signed-in">
          <UserButton appearance={{ elements: { avatarBox: "h-7 w-7" } }} />
        </Show>
      </div>
    </header>
  );
}
