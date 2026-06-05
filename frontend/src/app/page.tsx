import { GAME_REGISTRY } from "@/lib/gameRegistry";
import GameTile from "@/components/GameTile";

export default function Home() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-8 max-w-3xl mx-auto w-full">
      <h1 className="text-4xl font-bold text-amber-700 mb-2">Manneken</h1>
      <p className="text-lg text-amber-600 mb-8">Pick a game to play!</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 w-full">
        {GAME_REGISTRY.map((game) => (
          <GameTile key={game.id} game={game} />
        ))}
      </div>
    </main>
  );
}
