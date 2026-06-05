import Link from "next/link";
import { GameDefinition } from "@/lib/gameRegistry";

export default function GameTile({ game }: { game: GameDefinition }) {
  return (
    <Link href={game.path} className="group block">
      <div className="relative overflow-hidden bg-white/80 rounded-2xl border-2 border-amber-200 p-8 text-center transition-all duration-200 hover:scale-105 hover:shadow-lg hover:border-amber-400">
        <div
          className="absolute inset-x-0 top-0 h-1.5"
          style={{ backgroundColor: game.color }}
        />
        <div className="text-5xl mb-4">{game.emoji}</div>
        <h2 className="text-xl font-bold text-amber-700">{game.name}</h2>
        <p className="text-sm text-amber-600 mt-2">{game.description}</p>
      </div>
    </Link>
  );
}
