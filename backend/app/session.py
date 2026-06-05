from dataclasses import dataclass, field

MOODS = ["happy", "excited", "sad", "angry", "silly", "calm", "scared", "curious"]


@dataclass
class GameSession:
    conversation_history: list[dict] = field(default_factory=list)
    mood: str = "happy"
    gender: str = "boy"
    ttt_board: list[str] = field(default_factory=lambda: [""] * 9)
    ttt_board_size: int = 3
    ttt_active: bool = False
    ttt_player_symbol: str = "X"
    ttt_manneken_symbol: str = "O"

    def reset_chat(self):
        self.conversation_history.clear()
        self.mood = "happy"

    def reset_ttt(self, board_size: int = 3):
        self.ttt_board_size = board_size
        self.ttt_board = [""] * (board_size * board_size)
        self.ttt_active = True

    def add_message(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})

    def recent_messages(self, n: int = 20) -> list[dict]:
        return self.conversation_history[-n:]


session = GameSession()