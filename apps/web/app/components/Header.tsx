"use client";

import Link from "next/link";
import { UserMenu } from "./UserMenu";

export function Header() {
  return (
    <header className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/70 px-margin-mobile shadow-sm backdrop-blur-xl md:px-margin-desktop">
      <Link href="/" className="text-headline-lg font-bold tracking-tight text-on-surface hover:text-primary transition-colors">
        Atlas
      </Link>
      <UserMenu />
    </header>
  );
}
