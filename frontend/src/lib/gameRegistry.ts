export interface GameDefinition {
  id: string;
  name: string;
  emoji: string;
  description: string;
  path: string;
  color: string;
}

export const GAME_REGISTRY: GameDefinition[] = [
  {
    id: "dressup",
    name: "Dress Up",
    emoji: "👗",
    description: "Dress Manneken in fun outfits!",
    path: "/play/dressup",
    color: "#f6ad55",
  },
  {
    id: "tictactoe",
    name: "Tic Tac Toe",
    emoji: "❌⭕",
    description: "Play Tic Tac Toe against Manneken!",
    path: "/play/tictactoe",
    color: "#63b3ed",
  },
];
