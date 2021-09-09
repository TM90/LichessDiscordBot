import chess
import cairosvg
from datetime import datetime


class Board:
    def __init__(self, ident: str, fen: str) -> None:
        self._id = ident
        self._board = chess.Board(fen)
        self._last_move = chess.Move.null()
        self.last_change = datetime.now()

    def to_svg(self) -> str:
        cairosvg.svg2png(bytestring=chess.svg.board(self._board, lastmove=self._last_move), write_to=f"{self._id}.png")
        return f"{self._id}.png"

    def move(self, move_str: str) -> bool:
        move = chess.Move.from_uci(move_str)
        self.last_change = datetime.now()
        if move in self._board.legal_moves:
            self._last_move = move
            self._board.push(move)
            return True
        else:
            return False
