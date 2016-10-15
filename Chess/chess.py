# -*- coding: utf-8 -*-

import collections
import random
import re
import datetime
import itertools
import math
import plugin_super_class

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtSvg import *


START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def opposite_color(color):
    """:return: The opposite color.

    :param color:
        "w", "white, "b" or "black".
    """
    if color == "w":
        return "b"
    elif color == "white":
        return "black"
    elif color == "b":
        return "w"
    elif color == "black":
        return "white"
    else:
        raise ValueError("Expected w, b, white or black, got: %s." % color)


class Piece(object):
    """Representss a chess piece.

    :param symbol:
        THe symbol of the piece as used in `FENs <http://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation#Definition>`_.

    Piece objects that have the same type and color compare as equal.

    >>> import chess
    >>> chess.Piece("Q") == chess.Piece.from_color_and_type("w", "q")
    True
    """

    __cache = dict()

    def __init__(self, symbol):
        self.__symbol = symbol

        self.__color = "w" if symbol != symbol.lower() else "b"
        self.__full_color = "white" if self.__color == "w" else "black"

        self.__type = symbol.lower()
        if self.__type == "p":
            self.__full_type = "pawn"
        elif self.__type == "n":
            self.__full_type = "knight"
        elif self.__type == "b":
            self.__full_type = "bishop"
        elif self.__type == "r":
            self.__full_type = "rook"
        elif self.__type == "q":
            self.__full_type = "queen"
        elif self.__type == "k":
            self.__full_type = "king"
        else:
            raise ValueError("Expected valid piece symbol, got: %s." % symbol)

        self.__hash = ord(self.__symbol)

    @classmethod
    def from_color_and_type(cls, color, type):
        """Creates a piece object from color and type.

        An alternate way of creating pieces is from color and type.

        :param color:
            `"w"`, `"b"`, `"white"` or `"black"`.
        :param type:
            `"p"`, `"pawn"`, `"r"`, `"rook"`, `"n"`, `"knight"`, `"b"`,
            `"bishop"`, `"q"`, `"queen"`, `"k"` or `"king"`.

        >>> chess.Piece.from_color_and_type("w", "pawn")
        Piece('P')
        >>> chess.Piece.from_color_and_type("black", "q")
        Piece('q')
        """
        if type == "p" or type == "pawn":
            symbol = "p"
        elif type == "n" or type == "knight":
            symbol = "n"
        elif type == "b" or type == "bishop":
            symbol = "b"
        elif type == "r" or type == "rook":
            symbol = "r"
        elif type == "q" or type == "queen":
            symbol = "q"
        elif type == "k" or type == "king":
            symbol = "k"
        else:
            raise ValueError("Expected piece type, got: %s." % type)

        if color == "w" or color == "white":
            return cls(symbol.upper())
        elif color == "b" or color == "black":
            return cls(symbol)
        else:
            raise ValueError("Expected w, b, white or black, got: %s." % color)

    @property
    def symbol(self):
        """The symbol of the piece as used in `FENs <http://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation#Definition>`_."""
        return self.__symbol

    @property
    def color(self):
        """The color of the piece as `"b"` or `"w"`."""
        return self.__color

    @property
    def full_color(self):
        """The full color of the piece as `"black"` or `"white`."""
        return self.__full_color

    @property
    def type(self):
        """The type of the piece as `"p"`, `"b"`, `"n"`, `"r"`, `"k"`,
        or `"q"` for pawn, bishop, knight, rook, king or queen.
        """
        return self.__type

    @property
    def full_type(self):
        """The full type of the piece as `"pawn"`, `"bishop"`,
        `"knight"`, `"rook"`, `"king"` or `"queen"`.
        """
        return self.__full_type

    def __str__(self):
        return self.__symbol

    def __repr__(self):
        return "Piece('%s')" % self.__symbol

    def __eq__(self, other):
        return isinstance(other, Piece) and self.__symbol == other.symbol

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.__hash


class Square(object):
    """Represents a square on the chess board.

    :param name: The name of the square in algebraic notation.

    Square objects that represent the same square compare as equal.

    >>> import chess
    >>> chess.Square("e4") == chess.Square("e4")
    True
    """

    __cache = dict()

    def __init__(self, name):
        if not len(name) == 2:
            raise ValueError("Expected square name, got: %s." % repr(name))
        self.__name = name

        if not name[0] in ["a", "b", "c", "d", "e", "f", "g", "h"]:
            raise ValueError("Expected file, got: %s." % repr(name[0]))
        self.__file = name[0]
        self.__x = ord(self.__name[0]) - ord("a")

        if not name[1] in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            raise ValueError("Expected rank, got: %s." % repr(name[1]))
        self.__rank = int(name[1])
        self.__y = ord(self.__name[1]) - ord("1")

        self.__x88 = self.__x + 16 * (7 - self.__y)

    @classmethod
    def from_x88(cls, x88):
        """Creates a square object from an `x88 <http://en.wikipedia.org/wiki/Board_representation_(chess)#0x88_method>`_
        index.

        :param x88:
            The x88 index as integer between 0 and 128.
        """
        if x88 < 0 or x88 > 128:
            raise ValueError("x88 index is out of range: %s." % repr(x88))

        if x88 & 0x88:
            raise ValueError("x88 is not on the board: %s." % repr(x88))

        return cls("abcdefgh"[x88 & 7] + "87654321"[x88 >> 4])

    @classmethod
    def from_rank_and_file(cls, rank, file):
        """Creates a square object from rank and file.

        :param rank:
            An integer between 1 and 8.
        :param file:
            The rank as a letter between `"a"` and `"h"`.
        """
        if rank < 1 or rank > 8:
            raise ValueError("Expected rank to be between 1 and 8: %s." % repr(rank))

        if not file in ["a", "b", "c", "d", "e", "f", "g", "h"]:
            raise ValueError("Expected the file to be a letter between 'a' and 'h': %s." % repr(file))

        return cls(file + str(rank))

    @classmethod
    def from_x_and_y(cls, x, y):
        """Creates a square object from x and y coordinates.

        :param x:
            An integer between 0 and 7 where 0 is the a-file.
        :param y:
            An integer between 0 and 7 where 0 is the first rank.
        """
        return cls("abcdefgh"[x] + "12345678"[y])

    @property
    def name(self):
        """The algebraic name of the square."""
        return self.__name

    @property
    def file(self):
        """The file as a letter between `"a"` and `"h"`."""
        return self.__file

    @property
    def x(self):
        """The x-coordinate, starting with 0 for the a-file."""
        return self.__x

    @property
    def rank(self):
        """The rank as an integer between 1 and 8."""
        return self.__rank

    @property
    def y(self):
        """The y-coordinate, starting with 0 for the first rank."""
        return self.__y

    @property
    def x88(self):
        """The `x88 <http://en.wikipedia.org/wiki/Board_representation_(chess)#0x88_method>`_
        index of the square."""
        return self.__x88

    def is_dark(self):
        """:return: Whether it is a dark square."""
        return (self.__x - self.__y % 2) == 0

    def is_light(self):
        """:return: Whether it is a light square."""
        return not self.is_dark()

    def is_backrank(self):
        """:return: Whether the square is on either sides backrank."""
        return self.__y == 0 or self.__y == 7

    def __str__(self):
        return self.__name

    def __repr__(self):
        return "Square('%s')" % self.__name

    def __eq__(self, other):
        return isinstance(other, Square) and self.__name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.__x88


class Move(object):
    """Represents a move.

    :param source:
        The source square.
    :param target:
        The target square.
    :param promotion:
        Optional. If given this indicates which piece a pawn has been
        promoted to: `"r"`, `"n"`, `"b"` or `"q"`.

        Identical moves compare as equal.
    True
    """

    __uci_move_regex = re.compile(r"^([a-h][1-8])([a-h][1-8])([rnbq]?)$")

    def __init__(self, source, target, promotion=None):
        if not isinstance(source, Square):
            raise TypeError("Expected source to be a Square.")
        self.__source = source

        if not isinstance(target, Square):
            raise TypeError("Expected target to be a Square.")
        self.__target = target

        if not promotion:
            self.__promotion = None
            self.__full_promotion = None
        else:
            promotion = promotion.lower()
            if promotion == "n" or promotion == "knight":
                self.__promotion = "n"
                self.__full_promotion = "knight"
            elif promotion == "b" or promotion == "bishop":
                self.__promotion = "b"
                self.__full_promotion = "bishop"
            elif promotion == "r" or promotion == "rook":
                self.__promotion = "r"
                self.__full_promotion = "rook"
            elif promotion == "q" or promotion == "queen":
                self.__promotion = "q"
                self.__full_promotion = "queen"
            else:
                raise ValueError("Expected promotion type, got: %s." % repr(promotion))

    @classmethod
    def from_uci(cls, uci):
        """The UCI move string like `"a1a2"` or `"b7b8q"`."""
        if uci == "0000":
            return cls.get_null()

        match = cls.__uci_move_regex.match(uci)

        return cls(
            source=Square(match.group(1)),
            target=Square(match.group(2)),
            promotion=match.group(3) or None)

    @classmethod
    def get_null(cls):
        """:return: A null move."""
        return cls(Square("a1"), Square("a1"))

    @property
    def source(self):
        """The source square."""
        return self.__source

    @property
    def target(self):
        """The target square."""
        return self.__target

    @property
    def promotion(self):
        """The promotion type as `None`, `"r"`, `"n"`, `"b"` or `"q"`."""
        return self.__promotion

    @property
    def full_promotion(self):
        """Like `promotion`, but with full piece type names."""
        return self.__full_promotion

    @property
    def uci(self):
        """The UCI move string like `"a1a2"` or `"b7b8q"`."""
        if self.is_null():
            return "0000"
        else:
            if self.__promotion:
                return self.__source.name + self.__target.name + self.__promotion
            else:
                return self.__source.name + self.__target.name

    def is_null(self):
        """:return: Whether the move is a null move."""
        return self.__source == self.__target

    def __nonzero__(self):
        return not self.is_null()

    def __str__(self):
        return self.uci

    def __repr__(self):
        return "Move.from_uci(%s)" % repr(self.uci)

    def __eq__(self, other):
        return isinstance(other, Move) and self.uci == other.uci

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.uci)


MoveInfo = collections.namedtuple("MoveInfo", [
    "move",
    "piece",
    "captured",
    "san",
    "is_enpassant",
    "is_king_side_castle",
    "is_queen_side_castle",
    "is_castle",
    "is_check",
    "is_checkmate"])


class Position(object):
    """Represents a chess position.

    :param fen:
        Optional. The FEN of the position. Defaults to the standard
        chess start position.
    """

    __san_regex = re.compile('^([NBKRQ])?([a-h])?([1-8])?x?([a-h][1-8])(=[NBRQ])?(\+|#)?$')

    def __init__(self, fen=START_FEN):
        self.__castling = "KQkq"
        self.fen = fen

    def copy(self):
        """Gets a copy of the position. The copy will not change when the
        original instance is changed.

        :return:
            An exact copy of the positon.
        """
        return Position(self.fen)

    def __get_square_index(self, square_or_int):
        if type(square_or_int) is int:
            # Validate the index by passing it through the constructor.
            return Square.from_x88(square_or_int).x88
        elif isinstance(square_or_int, str):
            return Square(square_or_int).x88
        elif type(square_or_int) is Square:
            return square_or_int.x88
        else:
            raise TypeError(
                "Expected integer or Square, got: %s." % repr(square_or_int))

    def __getitem__(self, key):
        return self.__board[self.__get_square_index(key)]

    def __setitem__(self, key, value):
        if value is None or type(value) is Piece:
            self.__board[self.__get_square_index(key)] = value
        else:
            raise TypeError("Expected Piece or None, got: %s." % repr(value))

    def __delitem__(self, key):
        self.__board[self.__get_square_index(key)] = None

    def clear_board(self):
        """Removes all pieces from the board."""
        self.__board = [None] * 128

    def reset(self):
        """Resets to the standard chess start position."""
        self.set_fen(START_FEN)

    def __get_disambiguator(self, move):
        same_rank = False
        same_file = False
        piece = self[move.source]

        for m in self.get_legal_moves():
            ambig_piece = self[m.source]
            if (piece == ambig_piece and move.source != m.source and
                move.target == m.target):
                if move.source.rank == m.source.rank:
                    same_rank = True

                if move.source.file == m.source.file:
                    same_file = True

                if same_rank and same_file:
                    break

        if same_rank and same_file:
            return move.source.name
        elif same_file:
            return str(move.source.rank)
        elif same_rank:
            return move.source.file
        else:
            return ""

    def get_move_from_san(self, san):
        """Gets a move from standard algebraic notation.

        :param san:
            A move string in standard algebraic notation.

        :return:
            A Move object.

        :raise Exception:
            If not exactly one legal move matches.
        """
        # Castling moves.
        if san == "O-O" or san == "O-O-O":
            rank = 1 if self.turn == "w" else 8
            if san == "O-O":
                return Move(
                    source=Square.from_rank_and_file(rank, 'e'),
                    target=Square.from_rank_and_file(rank, 'g'))
            else:
                return Move(
                    source=Square.from_rank_and_file(rank, 'e'),
                    target=Square.from_rank_and_file(rank, 'c'))
        # Regular moves.
        else:
            matches = Position.__san_regex.match(san)
            if not matches:
                raise ValueError("Invalid SAN: %s." % repr(san))

            piece = Piece.from_color_and_type(
                color=self.turn,
                type=matches.group(1).lower() if matches.group(1) else 'p')
            target = Square(matches.group(4))

            source = None
            for m in self.get_legal_moves():
                if self[m.source] != piece or m.target != target:
                    continue

                if matches.group(2) and matches.group(2) != m.source.file:
                    continue
                if matches.group(3) and matches.group(3) != str(m.source.rank):
                    continue

                # Move matches. Assert it is not ambiguous.
                if source:
                    raise Exception(
                        "Move is ambiguous: %s matches %s and %s."
                            % san, source, m)
                source = m.source

            if not source:
                raise Exception("No legal move matches %s." % san)

            return Move(source, target, matches.group(5) or None)

    def get_move_info(self, move):
        """Gets information about a move.

        :param move:
            The move to get information about.

        :return:
            A named tuple with these properties:

            `move`:
                The move object.
            `piece`:
                The piece that has been moved.
            `san`:
                The standard algebraic notation of the move.
            `captured`:
                The piece that has been captured or `None`.
            `is_enpassant`:
                A boolean indicating if the move is an en-passant
                capture.
            `is_king_side_castle`:
                Whether it is a king-side castling move.
            `is_queen_side_castle`:
                Whether it is a queen-side castling move.
            `is_castle`:
                Whether it is a castling move.
            `is_check`:
                Whether the move gives check.
            `is_checkmate`:
                Whether the move gives checkmate.

        :raise Exception:
            If the move is not legal in the position.
        """
        resulting_position = self.copy().make_move(move)

        capture = self[move.target]
        piece = self[move.source]

        # Pawn moves.
        enpassant = False
        if piece.type == "p":
            # En-passant.
            if move.target.file != move.source.file and not capture:
                enpassant = True
                capture = Piece.from_color_and_type(
                    color=resulting_position.turn, type='p')

        # Castling.
        if piece.type == "k":
            is_king_side_castle = move.target.x - move.source.x == 2
            is_queen_side_castle = move.target.x - move.source.x == -2
        else:
            is_king_side_castle = is_queen_side_castle = False

        # Checks.
        is_check = resulting_position.is_check()
        is_checkmate = resulting_position.is_checkmate()

        # Generate the SAN.
        san = ""
        if is_king_side_castle:
            san += "o-o"
        elif is_queen_side_castle:
            san += "o-o-o"
        else:
            if piece.type != 'p':
                san += piece.type.upper()

            san += self.__get_disambiguator(move)

            if capture:
                if piece.type == 'p':
                    san += move.source.file
                san += "x"
            san += move.target.name

            if move.promotion:
                san += "="
                san += move.promotion.upper()

        if is_checkmate:
            san += "#"
        elif is_check:
            san += "+"

        if enpassant:
            san += " (e.p.)"

        # Return the named tuple.
        return MoveInfo(
            move=move,
            piece=piece,
            captured=capture,
            san=san,
            is_enpassant=enpassant,
            is_king_side_castle=is_king_side_castle,
            is_queen_side_castle=is_queen_side_castle,
            is_castle=is_king_side_castle or is_queen_side_castle,
            is_check=is_check,
            is_checkmate=is_checkmate)

    def make_move(self, move, validate=True):
        """Makes a move.

        :param move:
            The move to make.
        :param validate:
            Defaults to `True`. Whether the move should be validated.

        :return:
            Making a move changes the position object. The same
            (changed) object is returned for chainability.

        :raise Exception:
            If the validate parameter is `True` and the move is not
            legal in the position.
        """
        if validate and move not in self.get_legal_moves():
            raise Exception(
                "%s is not a legal move in the position %s." % (move, self.fen))
        piece = self[move.source]
        capture = self[move.target]

        # Move the piece.
        self[move.target] = self[move.source]
        del self[move.source]

        # It is the next players turn.
        self.toggle_turn()

        # Pawn moves.
        self.ep_file = None
        if piece.type == "p":
            # En-passant.
            if move.target.file != move.source.file and not capture:
                if self.turn == "w":
                    self[move.target.x88 - 16] = None
                else:
                    self[move.target.x88 + 16] = None
                capture = True
            # If big pawn move, set the en-passant file.
            if abs(move.target.rank - move.source.rank) == 2:
                if self.get_theoretical_ep_right(move.target.file):
                    self.ep_file = move.target.file

        # Promotion.
        if move.promotion:
            self[move.target] = Piece.from_color_and_type(
                color=piece.color, type=move.promotion)

        # Potential castling.
        if piece.type == "k":
            steps = move.target.x - move.source.x
            if abs(steps) == 2:
                # Queen-side castling.
                if steps == -2:
                    rook_target = move.target.x88 + 1
                    rook_source = move.target.x88 - 2
                # King-side castling.
                else:
                    rook_target = move.target.x88 - 1
                    rook_source = move.target.x88 + 1
                self[rook_target] = self[rook_source]
                del self[rook_source]

        # Increment the half move counter.
        if piece.type == "p" or capture:
            self.half_moves = 0
        else:
            self.half_moves += 1

        # Increment the move number.
        if self.turn == "w":
            self.ply += 1

        # Update castling rights.
        for type in ["K", "Q", "k", "q"]:
            if not self.get_theoretical_castling_right(type):
                self.set_castling_right(type, False)

        return self

    @property
    def turn(self):
        """Whos turn it is as `"w"` or `"b"`."""
        return self.__turn

    @turn.setter
    def turn(self, value):
        if value not in ["w", "b"]:
            raise ValueError(
                "Expected 'w' or 'b' for turn, got: %s." % repr(value))
        self.__turn = value

    def toggle_turn(self):
        """Toggles whos turn it is."""
        self.turn = opposite_color(self.turn)

    def get_castling_right(self, type):
        """Checks the castling rights.

        :param type:
            The castling move to check. "K" for king-side castling of
            the white player, "Q" for queen-side castling of the white
            player. "k" and "q" for the corresponding castling moves of
            the black player.

        :return:
            A boolean indicating whether the player has that castling
            right.
        """
        if not type in ["K", "Q", "k", "q"]:
            raise KeyError(
                "Expected 'K', 'Q', 'k' or 'q' as a castling type, got: %s." % repr(type))
        return type in self.__castling

    def get_theoretical_castling_right(self, type):
        """Checks if a player could have a castling right in theory from
        looking just at the piece positions.

        :param type:
            The castling move to check. See
            `Position.get_castling_right(type)` for values.

        :return:
            A boolean indicating whether the player could theoretically
            have that castling right.
        """
        if not type in ["K", "Q", "k", "q"]:
            raise KeyError(
                "Expected 'K', 'Q', 'k' or 'q' as a castling type, got: %s."
                    % repr(type))
        if type == "K" or type == "Q":
            if self["e1"] != Piece("K"):
                return False
            if type == "K":
                return self["h1"] == Piece("R")
            elif type == "Q":
                return self["a1"] == Piece("R")
        elif type == "k" or type == "q":
            if self["e8"] != Piece("k"):
                return False
            if type == "k":
                return self["h8"] == Piece("r")
            elif type == "q":
                return self["a8"] == Piece("r")

    def get_theoretical_ep_right(self, file):
        """Checks if a player could have an ep-move in theory from
        looking just at the piece positions.

        :param file:
            The file to check as a letter between `"a"` and `"h"`.

        :return:
            A boolean indicating whether the player could theoretically
            have that en-passant move.
        """
        if not file in ["a", "b", "c", "d", "e", "f", "g", "h"]:
            raise KeyError(
                "Expected a letter between 'a' and 'h' for the file, got: %s."
                    % repr(file))

        # Check there is a pawn.
        pawn_square = Square.from_rank_and_file(
            rank=4 if self.turn == "b" else 5, file=file)
        opposite_color_pawn = Piece.from_color_and_type(
            color=opposite_color(self.turn), type="p")
        if self[pawn_square] != opposite_color_pawn:
            return False

        # Check the square below is empty.
        square_below = Square.from_rank_and_file(
            rank=3 if self.turn == "b" else 6, file=file)
        if self[square_below]:
            return False

        # Check there is a pawn of the other color on a neighbor file.
        f = ord(file) - ord("a")
        p = Piece("p")
        P = Piece("P")
        if self.turn == "b":
            if f > 0 and self[Square.from_x_and_y(f - 1, 3)] == p:
                return True
            elif f < 7 and self[Square.from_x_and_y(f + 1, 3)] == p:
                return True
        else:
            if f > 0 and self[Square.from_x_and_y(f - 1, 4)] == P:
                return True
            elif f < 7 and self[Square.from_x_and_y(f + 1, 4)] == P:
                return True
        return False

    def set_castling_right(self, type, status):
        """Sets a castling right.

        :param type:
            `"K"`, `"Q"`, `"k"`, or `"q"` as used by
            `Position.get_castling_right(type)`.
        :param status:
            A boolean indicating whether that castling right should be
            granted or denied.
        """
        if not type in ["K", "Q", "k", "q"]:
            raise KeyError(
                "Expected 'K', 'Q', 'k' or 'q' as a castling type, got: %s."
                    % repr(type))

        castling = ""
        for t in ["K", "Q", "k", "q"]:
            if type == t:
                if status:
                    castling += t
            elif self.get_castling_right(t):
                castling += t
        self.__castling = castling

    @property
    def ep_file(self):
        """The en-passant file as a lowercase letter between `"a"` and
        `"h"` or `None`."""
        return self.__ep_file

    @ep_file.setter
    def ep_file(self, value):
        if not value in ["a", "b", "c", "d", "e", "f", "g", "h", None]:
            raise ValueError(
                "Expected None or a letter between 'a' and 'h' for the "
                "en-passant file, got: %s." % repr(value))

        self.__ep_file = value

    @property
    def half_moves(self):
        """The number of half-moves since the last capture or pawn move."""
        return self.__half_moves

    @half_moves.setter
    def half_moves(self, value):
        if type(value) is not int:
            raise TypeError(
                "Expected integer for half move count, got: %s." % repr(value))
        if value < 0:
            raise ValueError("Half move count must be >= 0.")

        self.__half_moves = value

    @property
    def ply(self):
        """The number of this move. The game starts at 1 and the counter
        is incremented every time white moves.
        """
        return self.__ply

    @ply.setter
    def ply(self, value):
        if type(value) is not int:
            raise TypeError(
                "Expected integer for ply count, got: %s." % repr(value))
        if value < 1:
            raise ValueError("Ply count must be >= 1.")
        self.__ply = value

    def get_piece_counts(self, color = "wb"):
        """Counts the pieces on the board.

        :param color:
            Defaults to `"wb"`. A color to filter the pieces by. Valid
            values are "w", "b", "wb" and "bw".

        :return:
            A dictionary of piece counts, keyed by lowercase piece type
            letters.
        """
        if not color in ["w", "b", "wb", "bw"]:
            raise KeyError(
                "Expected color filter to be one of 'w', 'b', 'wb', 'bw', "
                "got: %s." % repr(color))

        counts = {
            "p": 0,
            "b": 0,
            "n": 0,
            "r": 0,
            "k": 0,
            "q": 0,
        }
        for piece in self.__board:
            if piece and piece.color in color:
                counts[piece.type] += 1
        return counts

    def get_king(self, color):
        """Gets the square of the king.

        :param color:
            `"w"` for the white players king. `"b"` for the black
            players king.

        :return:
            The first square with a matching king or `None` if that
            player has no king.
        """
        if not color in ["w", "b"]:
            raise KeyError("Invalid color: %s." % repr(color))

        for x88, piece in enumerate(self.__board):
            if piece and piece.color == color and piece.type == "k":
                return Square.from_x88(x88)

    @property
    def fen(self):
        """The FEN string representing the position."""
        # Board setup.
        empty = 0
        fen = ""
        for y in range(7, -1, -1):
            for x in range(0, 8):
                square = Square.from_x_and_y(x, y)

                # Add pieces.
                if not self[square]:
                    empty += 1
                else:
                    if empty > 0:
                        fen += str(empty)
                        empty = 0
                    fen += self[square].symbol

            # Boarder of the board.
            if empty > 0:
                fen += str(empty)
            if not (x == 7 and y == 0):
                fen += "/"
            empty = 0

        if self.ep_file and self.get_theoretical_ep_right(self.ep_file):
            ep_square = self.ep_file + ("3" if self.turn == "b" else "6")
        else:
            ep_square = "-"

        # Join the parts together.
        return " ".join([
            fen,
            self.turn,
            self.__castling if self.__castling else "-",
            ep_square,
            str(self.half_moves),
            str(self.__ply)])

    @fen.setter
    def fen(self, fen):
        # Split into 6 parts.
        tokens = fen.split()
        if len(tokens) != 6:
            raise Exception("A FEN does not consist of 6 parts.")

        # Check that the position part is valid.
        rows = tokens[0].split("/")
        assert len(rows) == 8
        for row in rows:
            field_sum = 0
            previous_was_number = False
            for char in row:
                if char in "12345678":
                    if previous_was_number:
                        raise Exception(
                            "Position part of the FEN is invalid: "
                            "Multiple numbers immediately after each other.")
                    field_sum += int(char)
                    previous_was_number = True
                elif char in "pnbrkqPNBRKQ":
                    field_sum += 1
                    previous_was_number = False
                else:
                    raise Exception(
                        "Position part of the FEN is invalid: "
                        "Invalid character in the position part of the FEN.")

            if field_sum != 8:
                Exception(
                    "Position part of the FEN is invalid: "
                    "Row with invalid length.")

        # Check that the other parts are valid.
        if not tokens[1] in ["w", "b"]:
            raise Exception(
                "Turn part of the FEN is invalid: Expected b or w.")
        if not re.compile(r"^(KQ?k?q?|Qk?q?|kq?|q|-)$").match(tokens[2]):
            raise Exception("Castling part of the FEN is invalid.")
        if not re.compile(r"^(-|[a-h][36])$").match(tokens[3]):
            raise Exception("En-passant part of the FEN is invalid.")
        if not re.compile(r"^(0|[1-9][0-9]*)$").match(tokens[4]):
            raise Exception("Half move part of the FEN is invalid.")
        if not re.compile(r"^[1-9][0-9]*$").match(tokens[5]):
            raise Exception("Ply part of the FEN is invalid.")

        # Set pieces on the board.
        self.__board = [None] * 128
        i = 0
        for symbol in tokens[0]:
            if symbol == "/":
                i += 8
            elif symbol in "12345678":
                i += int(symbol)
            else:
                self.__board[i] = Piece(symbol)
                i += 1

        # Set the turn.
        self.__turn = tokens[1]

        # Set the castling rights.
        for type in ["K", "Q", "k", "q"]:
            self.set_castling_right(type, type in tokens[2])

        # Set the en-passant file.
        if tokens[3] == "-":
            self.__ep_file = None
        else:
            self.__ep_file = tokens[3][0]

        # Set the move counters.
        self.__half_moves = int(tokens[4])
        self.__ply = int(tokens[5])

    def is_king_attacked(self, color):
        """:return: Whether the king of the given color is attacked.

        :param color: `"w"` or `"b"`.
        """
        square = self.get_king(color)
        if square:
            return self.is_attacked(opposite_color(color), square)
        else:
            return False

    def get_pseudo_legal_moves(self):
        """:yield: Pseudo legal moves in the current position."""
        PAWN_OFFSETS = {
            "b": [16, 32, 17, 15],
            "w": [-16, -32, -17, -15]
        }

        PIECE_OFFSETS = {
            "n": [-18, -33, -31, -14, 18, 33, 31, 14],
            "b": [-17, -15, 17, 15],
            "r": [-16, 1, 16, -1],
            "q": [-17, -16, -15, 1, 17, 16, 15, -1],
            "k": [-17, -16, -15, 1, 17, 16, 15, -1]
        }

        for x88, piece in enumerate(self.__board):
            # Skip pieces of the opponent.
            if not piece or piece.color != self.turn:
                continue

            square = Square.from_x88(x88)

            # Pawn moves.
            if piece.type == "p":
                # Single square ahead. Do not capture.
                target = Square.from_x88(x88 + PAWN_OFFSETS[self.turn][0])
                if not self[target]:
                    # Promotion.
                    if target.is_backrank():
                        for promote_to in "bnrq":
                            yield Move(square, target, promote_to)
                    else:
                        yield Move(square, target)

                    # Two squares ahead. Do not capture.
                    if (self.turn == "w" and square.rank == 2) or (self.turn == "b" and square.rank == 7):
                        target = Square.from_x88(square.x88 + PAWN_OFFSETS[self.turn][1])
                        if not self[target]:
                            yield Move(square, target)

                # Pawn captures.
                for j in [2, 3]:
                   target_index = square.x88 + PAWN_OFFSETS[self.turn][j]
                   if target_index & 0x88:
                       continue
                   target = Square.from_x88(target_index)
                   if self[target] and self[target].color != self.turn:
                       # Promotion.
                       if target.is_backrank():
                           for promote_to in "bnrq":
                               yield Move(square, target, promote_to)
                       else:
                           yield Move(square, target)
                   # En-passant.
                   elif not self[target] and target.file == self.ep_file:
                       yield Move(square, target)
            # Other pieces.
            else:
                for offset in PIECE_OFFSETS[piece.type]:
                    target_index = square.x88
                    while True:
                        target_index += offset
                        if target_index & 0x88:
                            break
                        target = Square.from_x88(target_index)
                        if not self[target]:
                            yield Move(square, target)
                        else:
                            if self[target].color == self.turn:
                                break
                            yield Move(square, target)
                            break

                        # Knight and king do not go multiple times in their
                        # direction.
                        if piece.type in ["n", "k"]:
                            break

        opponent = opposite_color(self.turn)

        # King-side castling.
        k = "k" if self.turn == "b" else "K"
        if self.get_castling_right(k):
            of = self.get_king(self.turn).x88
            to = of + 2
            if not self[of + 1] and not self[to] and not self.is_check() and not self.is_attacked(opponent, Square.from_x88(of + 1)) and not self.is_attacked(opponent, Square.from_x88(to)):
                yield Move(Square.from_x88(of), Square.from_x88(to))

        # Queen-side castling
        q = "q" if self.turn == "b" else "Q"
        if self.get_castling_right(q):
            of = self.get_king(self.turn).x88
            to = of - 2

            if not self[of - 1] and not self[of - 2] and not self[of - 3] and not self.is_check() and not self.is_attacked(opponent, Square.from_x88(of - 1)) and not self.is_attacked(opponent, Square.from_x88(to)):
                yield Move(Square.from_x88(of), Square.from_x88(to))

    def get_legal_moves(self):
        """:yield: All legal moves in the current position."""
        for move in self.get_pseudo_legal_moves():
            potential_position = self.copy()
            potential_position.make_move(move, False)
            if not potential_position.is_king_attacked(self.turn):
                yield move

    def get_attackers(self, color, square):
        """Gets the attackers of a specific square.

        :param color:
            Filter attackers by this piece color.
        :param square:
            The square to check for.

        :yield:
            Source squares of the attack.
        """
        if color not in ["b", "w"]:
            raise KeyError("Invalid color: %s." % repr(color))

        ATTACKS = [
            20, 0, 0, 0, 0, 0, 0, 24, 0, 0, 0, 0, 0, 0, 20, 0,
            0, 20, 0, 0, 0, 0, 0, 24, 0, 0, 0, 0, 0, 20, 0, 0,
            0, 0, 20, 0, 0, 0, 0, 24, 0, 0, 0, 0, 20, 0, 0, 0,
            0, 0, 0, 20, 0, 0, 0, 24, 0, 0, 0, 20, 0, 0, 0, 0,
            0, 0, 0, 0, 20, 0, 0, 24, 0, 0, 20, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 20, 2, 24, 2, 20, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 2, 53, 56, 53, 2, 0, 0, 0, 0, 0, 0,
            24, 24, 24, 24, 24, 24, 56, 0, 56, 24, 24, 24, 24, 24, 24, 0,
            0, 0, 0, 0, 0, 2, 53, 56, 53, 2, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 20, 2, 24, 2, 20, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 20, 0, 0, 24, 0, 0, 20, 0, 0, 0, 0, 0,
            0, 0, 0, 20, 0, 0, 0, 24, 0, 0, 0, 20, 0, 0, 0, 0,
            0, 0, 20, 0, 0, 0, 0, 24, 0, 0, 0, 0, 20, 0, 0, 0,
            0, 20, 0, 0, 0, 0, 0, 24, 0, 0, 0, 0, 0, 20, 0, 0,
            20, 0, 0, 0, 0, 0, 0, 24, 0, 0, 0, 0, 0, 0, 20
        ]

        RAYS = [
            17, 0, 0, 0, 0, 0, 0, 16, 0, 0, 0, 0, 0, 0, 15, 0,
            0, 17, 0, 0, 0, 0, 0, 16, 0, 0, 0, 0, 0, 15, 0, 0,
            0, 0, 17, 0, 0, 0, 0, 16, 0, 0, 0, 0, 15, 0, 0, 0,
            0, 0, 0, 17, 0, 0, 0, 16, 0, 0, 0, 15, 0, 0, 0, 0,
            0, 0, 0, 0, 17, 0, 0, 16, 0, 0, 15, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 17, 0, 16, 0, 15, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 17, 16, 15, 0, 0, 0, 0, 0, 0, 0,
            1, 1, 1, 1, 1, 1, 1, 0, -1, -1, -1, -1, -1, -1, -1, 0,
            0, 0, 0, 0, 0, 0, -15, -16, -17, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, -15, 0, -16, 0, -17, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, -15, 0, 0, -16, 0, 0, -17, 0, 0, 0, 0, 0,
            0, 0, 0, -15, 0, 0, 0, -16, 0, 0, 0, -17, 0, 0, 0, 0,
            0, 0, -15, 0, 0, 0, 0, -16, 0, 0, 0, 0, -17, 0, 0, 0,
            0, -15, 0, 0, 0, 0, 0, -16, 0, 0, 0, 0, 0, -17, 0, 0,
            -15, 0, 0, 0, 0, 0, 0, -16, 0, 0, 0, 0, 0, 0, -17
        ]

        SHIFTS = {
            "p": 0,
            "n": 1,
            "b": 2,
            "r": 3,
            "q": 4,
            "k": 5
        }

        for x88, piece in enumerate(self.__board):
            if not piece or piece.color != color:
                continue
            source = Square.from_x88(x88)

            difference = source.x88 - square.x88
            index = difference + 119

            if ATTACKS[index] & (1 << SHIFTS[piece.type]):
                # Handle pawns.
                if piece.type == "p":
                    if difference > 0:
                        if piece.color == "w":
                            yield source
                    else:
                        if piece.color == "b":
                            yield source
                    continue

                # Handle knights and king.
                if piece.type in ["n", "k"]:
                    yield source

                # Handle the others.
                offset = RAYS[index]
                j = source.x88 + offset
                blocked = False
                while j != square.x88:
                    if self[j]:
                        blocked = True
                        break
                    j += offset
                if not blocked:
                    yield source

    def is_attacked(self, color, square):
        """Checks whether a square is attacked.

        :param color:
            Check if this player is attacking.
        :param square:
            The square the player might be attacking.

        :return:
            A boolean indicating whether the given square is attacked
            by the player of the given color.
        """
        x = list(self.get_attackers(color, square))
        return len(x) > 0

    def is_check(self):
        """:return: Whether the current player is in check."""
        return self.is_king_attacked(self.turn)

    def is_checkmate(self):
        """:return: Whether the current player has been checkmated."""
        if not self.is_check():
            return False
        else:
            arr = list(self.get_legal_moves())
            return len(arr) == 0

    def is_stalemate(self):
        """:return: Whether the current player is in stalemate."""
        if self.is_check():
            return False
        else:
            arr = list(self.get_legal_moves())
            return len(arr) == 0

    def is_insufficient_material(self):
        """Checks if there is sufficient material to mate.

        Mating is impossible in:

        * A king versus king endgame.
        * A king with bishop versus king endgame.
        * A king with knight versus king endgame.
        * A king with bishop versus king with bishop endgame, where both
          bishops are on the same color. Same goes for additional
          bishops on the same color.

        Assumes that the position is valid and each player has exactly
        one king.

        :return:
            Whether there is insufficient material to mate.
        """
        piece_counts = self.get_piece_counts()
        if sum(piece_counts.values()) == 2:
            # King versus king.
            return True
        elif sum(piece_counts.values()) == 3:
            # King and knight or bishop versus king.
            if piece_counts["b"] == 1 or piece_counts["n"] == 1:
                return True
        elif sum(piece_counts.values()) == 2 + piece_counts["b"]:
            # Each player with only king and any number of bishops, where all
            # bishops are on the same color.
            white_has_bishop = self.get_piece_counts("w")["b"] != 0
            black_has_bishop = self.get_piece_counts("b")["b"] != 0
            if white_has_bishop and black_has_bishop:
                color = None
                for x88, piece in enumerate(self.__board):
                    if piece and piece.type == "b":
                        square = Square.from_x88(x88)
                        if color is not None and color != square.is_light():
                            return False
                        color = square.is_light()
                return True
        return False

    def is_game_over(self):
        """Checks if the game is over.

        :return:
            Whether the game is over by the rules of chess,
            disregarding that players can agree on a draw, claim a draw
            or resign.
        """
        return (self.is_checkmate() or self.is_stalemate() or
                self.is_insufficient_material())

    def __str__(self):
        return self.fen

    def __repr__(self):
        return "Position.from_fen(%s)" % repr(self.fen)

    def __eq__(self, other):
        return self.fen == other.fen

    def __ne__(self, other):
        return self.fen != other.fen

    def __hash__(self):
        hasher = ZobristHasher(ZobristHasher.POLYGLOT_RANDOM_ARRAY)
        return hasher.hash_position(self)


class ZobristHasher(object):
    """Represents a zobrist-hash function.

    :param random_array:
        An tuple or list of 781 random 64 bit integers.

    `POLYGLOT_RANDOM_ARRAY`:
        A tuple of 781 random numbers as used by the Polyglot opening
        book format.
    """

    POLYGLOT_RANDOM_ARRAY = (
        0x9D39247E33776D41, 0x2AF7398005AAA5C7, 0x44DB015024623547,
        0x9C15F73E62A76AE2, 0x75834465489C0C89, 0x3290AC3A203001BF,
        0x0FBBAD1F61042279, 0xE83A908FF2FB60CA, 0x0D7E765D58755C10,
        0x1A083822CEAFE02D, 0x9605D5F0E25EC3B0, 0xD021FF5CD13A2ED5,
        0x40BDF15D4A672E32, 0x011355146FD56395, 0x5DB4832046F3D9E5,
        0x239F8B2D7FF719CC, 0x05D1A1AE85B49AA1, 0x679F848F6E8FC971,
        0x7449BBFF801FED0B, 0x7D11CDB1C3B7ADF0, 0x82C7709E781EB7CC,
        0xF3218F1C9510786C, 0x331478F3AF51BBE6, 0x4BB38DE5E7219443,
        0xAA649C6EBCFD50FC, 0x8DBD98A352AFD40B, 0x87D2074B81D79217,
        0x19F3C751D3E92AE1, 0xB4AB30F062B19ABF, 0x7B0500AC42047AC4,
        0xC9452CA81A09D85D, 0x24AA6C514DA27500, 0x4C9F34427501B447,
        0x14A68FD73C910841, 0xA71B9B83461CBD93, 0x03488B95B0F1850F,
        0x637B2B34FF93C040, 0x09D1BC9A3DD90A94, 0x3575668334A1DD3B,
        0x735E2B97A4C45A23, 0x18727070F1BD400B, 0x1FCBACD259BF02E7,
        0xD310A7C2CE9B6555, 0xBF983FE0FE5D8244, 0x9F74D14F7454A824,
        0x51EBDC4AB9BA3035, 0x5C82C505DB9AB0FA, 0xFCF7FE8A3430B241,
        0x3253A729B9BA3DDE, 0x8C74C368081B3075, 0xB9BC6C87167C33E7,
        0x7EF48F2B83024E20, 0x11D505D4C351BD7F, 0x6568FCA92C76A243,
        0x4DE0B0F40F32A7B8, 0x96D693460CC37E5D, 0x42E240CB63689F2F,
        0x6D2BDCDAE2919661, 0x42880B0236E4D951, 0x5F0F4A5898171BB6,
        0x39F890F579F92F88, 0x93C5B5F47356388B, 0x63DC359D8D231B78,
        0xEC16CA8AEA98AD76, 0x5355F900C2A82DC7, 0x07FB9F855A997142,
        0x5093417AA8A7ED5E, 0x7BCBC38DA25A7F3C, 0x19FC8A768CF4B6D4,
        0x637A7780DECFC0D9, 0x8249A47AEE0E41F7, 0x79AD695501E7D1E8,
        0x14ACBAF4777D5776, 0xF145B6BECCDEA195, 0xDABF2AC8201752FC,
        0x24C3C94DF9C8D3F6, 0xBB6E2924F03912EA, 0x0CE26C0B95C980D9,
        0xA49CD132BFBF7CC4, 0xE99D662AF4243939, 0x27E6AD7891165C3F,
        0x8535F040B9744FF1, 0x54B3F4FA5F40D873, 0x72B12C32127FED2B,
        0xEE954D3C7B411F47, 0x9A85AC909A24EAA1, 0x70AC4CD9F04F21F5,
        0xF9B89D3E99A075C2, 0x87B3E2B2B5C907B1, 0xA366E5B8C54F48B8,
        0xAE4A9346CC3F7CF2, 0x1920C04D47267BBD, 0x87BF02C6B49E2AE9,
        0x092237AC237F3859, 0xFF07F64EF8ED14D0, 0x8DE8DCA9F03CC54E,
        0x9C1633264DB49C89, 0xB3F22C3D0B0B38ED, 0x390E5FB44D01144B,
        0x5BFEA5B4712768E9, 0x1E1032911FA78984, 0x9A74ACB964E78CB3,
        0x4F80F7A035DAFB04, 0x6304D09A0B3738C4, 0x2171E64683023A08,
        0x5B9B63EB9CEFF80C, 0x506AACF489889342, 0x1881AFC9A3A701D6,
        0x6503080440750644, 0xDFD395339CDBF4A7, 0xEF927DBCF00C20F2,
        0x7B32F7D1E03680EC, 0xB9FD7620E7316243, 0x05A7E8A57DB91B77,
        0xB5889C6E15630A75, 0x4A750A09CE9573F7, 0xCF464CEC899A2F8A,
        0xF538639CE705B824, 0x3C79A0FF5580EF7F, 0xEDE6C87F8477609D,
        0x799E81F05BC93F31, 0x86536B8CF3428A8C, 0x97D7374C60087B73,
        0xA246637CFF328532, 0x043FCAE60CC0EBA0, 0x920E449535DD359E,
        0x70EB093B15B290CC, 0x73A1921916591CBD, 0x56436C9FE1A1AA8D,
        0xEFAC4B70633B8F81, 0xBB215798D45DF7AF, 0x45F20042F24F1768,
        0x930F80F4E8EB7462, 0xFF6712FFCFD75EA1, 0xAE623FD67468AA70,
        0xDD2C5BC84BC8D8FC, 0x7EED120D54CF2DD9, 0x22FE545401165F1C,
        0xC91800E98FB99929, 0x808BD68E6AC10365, 0xDEC468145B7605F6,
        0x1BEDE3A3AEF53302, 0x43539603D6C55602, 0xAA969B5C691CCB7A,
        0xA87832D392EFEE56, 0x65942C7B3C7E11AE, 0xDED2D633CAD004F6,
        0x21F08570F420E565, 0xB415938D7DA94E3C, 0x91B859E59ECB6350,
        0x10CFF333E0ED804A, 0x28AED140BE0BB7DD, 0xC5CC1D89724FA456,
        0x5648F680F11A2741, 0x2D255069F0B7DAB3, 0x9BC5A38EF729ABD4,
        0xEF2F054308F6A2BC, 0xAF2042F5CC5C2858, 0x480412BAB7F5BE2A,
        0xAEF3AF4A563DFE43, 0x19AFE59AE451497F, 0x52593803DFF1E840,
        0xF4F076E65F2CE6F0, 0x11379625747D5AF3, 0xBCE5D2248682C115,
        0x9DA4243DE836994F, 0x066F70B33FE09017, 0x4DC4DE189B671A1C,
        0x51039AB7712457C3, 0xC07A3F80C31FB4B4, 0xB46EE9C5E64A6E7C,
        0xB3819A42ABE61C87, 0x21A007933A522A20, 0x2DF16F761598AA4F,
        0x763C4A1371B368FD, 0xF793C46702E086A0, 0xD7288E012AEB8D31,
        0xDE336A2A4BC1C44B, 0x0BF692B38D079F23, 0x2C604A7A177326B3,
        0x4850E73E03EB6064, 0xCFC447F1E53C8E1B, 0xB05CA3F564268D99,
        0x9AE182C8BC9474E8, 0xA4FC4BD4FC5558CA, 0xE755178D58FC4E76,
        0x69B97DB1A4C03DFE, 0xF9B5B7C4ACC67C96, 0xFC6A82D64B8655FB,
        0x9C684CB6C4D24417, 0x8EC97D2917456ED0, 0x6703DF9D2924E97E,
        0xC547F57E42A7444E, 0x78E37644E7CAD29E, 0xFE9A44E9362F05FA,
        0x08BD35CC38336615, 0x9315E5EB3A129ACE, 0x94061B871E04DF75,
        0xDF1D9F9D784BA010, 0x3BBA57B68871B59D, 0xD2B7ADEEDED1F73F,
        0xF7A255D83BC373F8, 0xD7F4F2448C0CEB81, 0xD95BE88CD210FFA7,
        0x336F52F8FF4728E7, 0xA74049DAC312AC71, 0xA2F61BB6E437FDB5,
        0x4F2A5CB07F6A35B3, 0x87D380BDA5BF7859, 0x16B9F7E06C453A21,
        0x7BA2484C8A0FD54E, 0xF3A678CAD9A2E38C, 0x39B0BF7DDE437BA2,
        0xFCAF55C1BF8A4424, 0x18FCF680573FA594, 0x4C0563B89F495AC3,
        0x40E087931A00930D, 0x8CFFA9412EB642C1, 0x68CA39053261169F,
        0x7A1EE967D27579E2, 0x9D1D60E5076F5B6F, 0x3810E399B6F65BA2,
        0x32095B6D4AB5F9B1, 0x35CAB62109DD038A, 0xA90B24499FCFAFB1,
        0x77A225A07CC2C6BD, 0x513E5E634C70E331, 0x4361C0CA3F692F12,
        0xD941ACA44B20A45B, 0x528F7C8602C5807B, 0x52AB92BEB9613989,
        0x9D1DFA2EFC557F73, 0x722FF175F572C348, 0x1D1260A51107FE97,
        0x7A249A57EC0C9BA2, 0x04208FE9E8F7F2D6, 0x5A110C6058B920A0,
        0x0CD9A497658A5698, 0x56FD23C8F9715A4C, 0x284C847B9D887AAE,
        0x04FEABFBBDB619CB, 0x742E1E651C60BA83, 0x9A9632E65904AD3C,
        0x881B82A13B51B9E2, 0x506E6744CD974924, 0xB0183DB56FFC6A79,
        0x0ED9B915C66ED37E, 0x5E11E86D5873D484, 0xF678647E3519AC6E,
        0x1B85D488D0F20CC5, 0xDAB9FE6525D89021, 0x0D151D86ADB73615,
        0xA865A54EDCC0F019, 0x93C42566AEF98FFB, 0x99E7AFEABE000731,
        0x48CBFF086DDF285A, 0x7F9B6AF1EBF78BAF, 0x58627E1A149BBA21,
        0x2CD16E2ABD791E33, 0xD363EFF5F0977996, 0x0CE2A38C344A6EED,
        0x1A804AADB9CFA741, 0x907F30421D78C5DE, 0x501F65EDB3034D07,
        0x37624AE5A48FA6E9, 0x957BAF61700CFF4E, 0x3A6C27934E31188A,
        0xD49503536ABCA345, 0x088E049589C432E0, 0xF943AEE7FEBF21B8,
        0x6C3B8E3E336139D3, 0x364F6FFA464EE52E, 0xD60F6DCEDC314222,
        0x56963B0DCA418FC0, 0x16F50EDF91E513AF, 0xEF1955914B609F93,
        0x565601C0364E3228, 0xECB53939887E8175, 0xBAC7A9A18531294B,
        0xB344C470397BBA52, 0x65D34954DAF3CEBD, 0xB4B81B3FA97511E2,
        0xB422061193D6F6A7, 0x071582401C38434D, 0x7A13F18BBEDC4FF5,
        0xBC4097B116C524D2, 0x59B97885E2F2EA28, 0x99170A5DC3115544,
        0x6F423357E7C6A9F9, 0x325928EE6E6F8794, 0xD0E4366228B03343,
        0x565C31F7DE89EA27, 0x30F5611484119414, 0xD873DB391292ED4F,
        0x7BD94E1D8E17DEBC, 0xC7D9F16864A76E94, 0x947AE053EE56E63C,
        0xC8C93882F9475F5F, 0x3A9BF55BA91F81CA, 0xD9A11FBB3D9808E4,
        0x0FD22063EDC29FCA, 0xB3F256D8ACA0B0B9, 0xB03031A8B4516E84,
        0x35DD37D5871448AF, 0xE9F6082B05542E4E, 0xEBFAFA33D7254B59,
        0x9255ABB50D532280, 0xB9AB4CE57F2D34F3, 0x693501D628297551,
        0xC62C58F97DD949BF, 0xCD454F8F19C5126A, 0xBBE83F4ECC2BDECB,
        0xDC842B7E2819E230, 0xBA89142E007503B8, 0xA3BC941D0A5061CB,
        0xE9F6760E32CD8021, 0x09C7E552BC76492F, 0x852F54934DA55CC9,
        0x8107FCCF064FCF56, 0x098954D51FFF6580, 0x23B70EDB1955C4BF,
        0xC330DE426430F69D, 0x4715ED43E8A45C0A, 0xA8D7E4DAB780A08D,
        0x0572B974F03CE0BB, 0xB57D2E985E1419C7, 0xE8D9ECBE2CF3D73F,
        0x2FE4B17170E59750, 0x11317BA87905E790, 0x7FBF21EC8A1F45EC,
        0x1725CABFCB045B00, 0x964E915CD5E2B207, 0x3E2B8BCBF016D66D,
        0xBE7444E39328A0AC, 0xF85B2B4FBCDE44B7, 0x49353FEA39BA63B1,
        0x1DD01AAFCD53486A, 0x1FCA8A92FD719F85, 0xFC7C95D827357AFA,
        0x18A6A990C8B35EBD, 0xCCCB7005C6B9C28D, 0x3BDBB92C43B17F26,
        0xAA70B5B4F89695A2, 0xE94C39A54A98307F, 0xB7A0B174CFF6F36E,
        0xD4DBA84729AF48AD, 0x2E18BC1AD9704A68, 0x2DE0966DAF2F8B1C,
        0xB9C11D5B1E43A07E, 0x64972D68DEE33360, 0x94628D38D0C20584,
        0xDBC0D2B6AB90A559, 0xD2733C4335C6A72F, 0x7E75D99D94A70F4D,
        0x6CED1983376FA72B, 0x97FCAACBF030BC24, 0x7B77497B32503B12,
        0x8547EDDFB81CCB94, 0x79999CDFF70902CB, 0xCFFE1939438E9B24,
        0x829626E3892D95D7, 0x92FAE24291F2B3F1, 0x63E22C147B9C3403,
        0xC678B6D860284A1C, 0x5873888850659AE7, 0x0981DCD296A8736D,
        0x9F65789A6509A440, 0x9FF38FED72E9052F, 0xE479EE5B9930578C,
        0xE7F28ECD2D49EECD, 0x56C074A581EA17FE, 0x5544F7D774B14AEF,
        0x7B3F0195FC6F290F, 0x12153635B2C0CF57, 0x7F5126DBBA5E0CA7,
        0x7A76956C3EAFB413, 0x3D5774A11D31AB39, 0x8A1B083821F40CB4,
        0x7B4A38E32537DF62, 0x950113646D1D6E03, 0x4DA8979A0041E8A9,
        0x3BC36E078F7515D7, 0x5D0A12F27AD310D1, 0x7F9D1A2E1EBE1327,
        0xDA3A361B1C5157B1, 0xDCDD7D20903D0C25, 0x36833336D068F707,
        0xCE68341F79893389, 0xAB9090168DD05F34, 0x43954B3252DC25E5,
        0xB438C2B67F98E5E9, 0x10DCD78E3851A492, 0xDBC27AB5447822BF,
        0x9B3CDB65F82CA382, 0xB67B7896167B4C84, 0xBFCED1B0048EAC50,
        0xA9119B60369FFEBD, 0x1FFF7AC80904BF45, 0xAC12FB171817EEE7,
        0xAF08DA9177DDA93D, 0x1B0CAB936E65C744, 0xB559EB1D04E5E932,
        0xC37B45B3F8D6F2BA, 0xC3A9DC228CAAC9E9, 0xF3B8B6675A6507FF,
        0x9FC477DE4ED681DA, 0x67378D8ECCEF96CB, 0x6DD856D94D259236,
        0xA319CE15B0B4DB31, 0x073973751F12DD5E, 0x8A8E849EB32781A5,
        0xE1925C71285279F5, 0x74C04BF1790C0EFE, 0x4DDA48153C94938A,
        0x9D266D6A1CC0542C, 0x7440FB816508C4FE, 0x13328503DF48229F,
        0xD6BF7BAEE43CAC40, 0x4838D65F6EF6748F, 0x1E152328F3318DEA,
        0x8F8419A348F296BF, 0x72C8834A5957B511, 0xD7A023A73260B45C,
        0x94EBC8ABCFB56DAE, 0x9FC10D0F989993E0, 0xDE68A2355B93CAE6,
        0xA44CFE79AE538BBE, 0x9D1D84FCCE371425, 0x51D2B1AB2DDFB636,
        0x2FD7E4B9E72CD38C, 0x65CA5B96B7552210, 0xDD69A0D8AB3B546D,
        0x604D51B25FBF70E2, 0x73AA8A564FB7AC9E, 0x1A8C1E992B941148,
        0xAAC40A2703D9BEA0, 0x764DBEAE7FA4F3A6, 0x1E99B96E70A9BE8B,
        0x2C5E9DEB57EF4743, 0x3A938FEE32D29981, 0x26E6DB8FFDF5ADFE,
        0x469356C504EC9F9D, 0xC8763C5B08D1908C, 0x3F6C6AF859D80055,
        0x7F7CC39420A3A545, 0x9BFB227EBDF4C5CE, 0x89039D79D6FC5C5C,
        0x8FE88B57305E2AB6, 0xA09E8C8C35AB96DE, 0xFA7E393983325753,
        0xD6B6D0ECC617C699, 0xDFEA21EA9E7557E3, 0xB67C1FA481680AF8,
        0xCA1E3785A9E724E5, 0x1CFC8BED0D681639, 0xD18D8549D140CAEA,
        0x4ED0FE7E9DC91335, 0xE4DBF0634473F5D2, 0x1761F93A44D5AEFE,
        0x53898E4C3910DA55, 0x734DE8181F6EC39A, 0x2680B122BAA28D97,
        0x298AF231C85BAFAB, 0x7983EED3740847D5, 0x66C1A2A1A60CD889,
        0x9E17E49642A3E4C1, 0xEDB454E7BADC0805, 0x50B704CAB602C329,
        0x4CC317FB9CDDD023, 0x66B4835D9EAFEA22, 0x219B97E26FFC81BD,
        0x261E4E4C0A333A9D, 0x1FE2CCA76517DB90, 0xD7504DFA8816EDBB,
        0xB9571FA04DC089C8, 0x1DDC0325259B27DE, 0xCF3F4688801EB9AA,
        0xF4F5D05C10CAB243, 0x38B6525C21A42B0E, 0x36F60E2BA4FA6800,
        0xEB3593803173E0CE, 0x9C4CD6257C5A3603, 0xAF0C317D32ADAA8A,
        0x258E5A80C7204C4B, 0x8B889D624D44885D, 0xF4D14597E660F855,
        0xD4347F66EC8941C3, 0xE699ED85B0DFB40D, 0x2472F6207C2D0484,
        0xC2A1E7B5B459AEB5, 0xAB4F6451CC1D45EC, 0x63767572AE3D6174,
        0xA59E0BD101731A28, 0x116D0016CB948F09, 0x2CF9C8CA052F6E9F,
        0x0B090A7560A968E3, 0xABEEDDB2DDE06FF1, 0x58EFC10B06A2068D,
        0xC6E57A78FBD986E0, 0x2EAB8CA63CE802D7, 0x14A195640116F336,
        0x7C0828DD624EC390, 0xD74BBE77E6116AC7, 0x804456AF10F5FB53,
        0xEBE9EA2ADF4321C7, 0x03219A39EE587A30, 0x49787FEF17AF9924,
        0xA1E9300CD8520548, 0x5B45E522E4B1B4EF, 0xB49C3B3995091A36,
        0xD4490AD526F14431, 0x12A8F216AF9418C2, 0x001F837CC7350524,
        0x1877B51E57A764D5, 0xA2853B80F17F58EE, 0x993E1DE72D36D310,
        0xB3598080CE64A656, 0x252F59CF0D9F04BB, 0xD23C8E176D113600,
        0x1BDA0492E7E4586E, 0x21E0BD5026C619BF, 0x3B097ADAF088F94E,
        0x8D14DEDB30BE846E, 0xF95CFFA23AF5F6F4, 0x3871700761B3F743,
        0xCA672B91E9E4FA16, 0x64C8E531BFF53B55, 0x241260ED4AD1E87D,
        0x106C09B972D2E822, 0x7FBA195410E5CA30, 0x7884D9BC6CB569D8,
        0x0647DFEDCD894A29, 0x63573FF03E224774, 0x4FC8E9560F91B123,
        0x1DB956E450275779, 0xB8D91274B9E9D4FB, 0xA2EBEE47E2FBFCE1,
        0xD9F1F30CCD97FB09, 0xEFED53D75FD64E6B, 0x2E6D02C36017F67F,
        0xA9AA4D20DB084E9B, 0xB64BE8D8B25396C1, 0x70CB6AF7C2D5BCF0,
        0x98F076A4F7A2322E, 0xBF84470805E69B5F, 0x94C3251F06F90CF3,
        0x3E003E616A6591E9, 0xB925A6CD0421AFF3, 0x61BDD1307C66E300,
        0xBF8D5108E27E0D48, 0x240AB57A8B888B20, 0xFC87614BAF287E07,
        0xEF02CDD06FFDB432, 0xA1082C0466DF6C0A, 0x8215E577001332C8,
        0xD39BB9C3A48DB6CF, 0x2738259634305C14, 0x61CF4F94C97DF93D,
        0x1B6BACA2AE4E125B, 0x758F450C88572E0B, 0x959F587D507A8359,
        0xB063E962E045F54D, 0x60E8ED72C0DFF5D1, 0x7B64978555326F9F,
        0xFD080D236DA814BA, 0x8C90FD9B083F4558, 0x106F72FE81E2C590,
        0x7976033A39F7D952, 0xA4EC0132764CA04B, 0x733EA705FAE4FA77,
        0xB4D8F77BC3E56167, 0x9E21F4F903B33FD9, 0x9D765E419FB69F6D,
        0xD30C088BA61EA5EF, 0x5D94337FBFAF7F5B, 0x1A4E4822EB4D7A59,
        0x6FFE73E81B637FB3, 0xDDF957BC36D8B9CA, 0x64D0E29EEA8838B3,
        0x08DD9BDFD96B9F63, 0x087E79E5A57D1D13, 0xE328E230E3E2B3FB,
        0x1C2559E30F0946BE, 0x720BF5F26F4D2EAA, 0xB0774D261CC609DB,
        0x443F64EC5A371195, 0x4112CF68649A260E, 0xD813F2FAB7F5C5CA,
        0x660D3257380841EE, 0x59AC2C7873F910A3, 0xE846963877671A17,
        0x93B633ABFA3469F8, 0xC0C0F5A60EF4CDCF, 0xCAF21ECD4377B28C,
        0x57277707199B8175, 0x506C11B9D90E8B1D, 0xD83CC2687A19255F,
        0x4A29C6465A314CD1, 0xED2DF21216235097, 0xB5635C95FF7296E2,
        0x22AF003AB672E811, 0x52E762596BF68235, 0x9AEBA33AC6ECC6B0,
        0x944F6DE09134DFB6, 0x6C47BEC883A7DE39, 0x6AD047C430A12104,
        0xA5B1CFDBA0AB4067, 0x7C45D833AFF07862, 0x5092EF950A16DA0B,
        0x9338E69C052B8E7B, 0x455A4B4CFE30E3F5, 0x6B02E63195AD0CF8,
        0x6B17B224BAD6BF27, 0xD1E0CCD25BB9C169, 0xDE0C89A556B9AE70,
        0x50065E535A213CF6, 0x9C1169FA2777B874, 0x78EDEFD694AF1EED,
        0x6DC93D9526A50E68, 0xEE97F453F06791ED, 0x32AB0EDB696703D3,
        0x3A6853C7E70757A7, 0x31865CED6120F37D, 0x67FEF95D92607890,
        0x1F2B1D1F15F6DC9C, 0xB69E38A8965C6B65, 0xAA9119FF184CCCF4,
        0xF43C732873F24C13, 0xFB4A3D794A9A80D2, 0x3550C2321FD6109C,
        0x371F77E76BB8417E, 0x6BFA9AAE5EC05779, 0xCD04F3FF001A4778,
        0xE3273522064480CA, 0x9F91508BFFCFC14A, 0x049A7F41061A9E60,
        0xFCB6BE43A9F2FE9B, 0x08DE8A1C7797DA9B, 0x8F9887E6078735A1,
        0xB5B4071DBFC73A66, 0x230E343DFBA08D33, 0x43ED7F5A0FAE657D,
        0x3A88A0FBBCB05C63, 0x21874B8B4D2DBC4F, 0x1BDEA12E35F6A8C9,
        0x53C065C6C8E63528, 0xE34A1D250E7A8D6B, 0xD6B04D3B7651DD7E,
        0x5E90277E7CB39E2D, 0x2C046F22062DC67D, 0xB10BB459132D0A26,
        0x3FA9DDFB67E2F199, 0x0E09B88E1914F7AF, 0x10E8B35AF3EEAB37,
        0x9EEDECA8E272B933, 0xD4C718BC4AE8AE5F, 0x81536D601170FC20,
        0x91B534F885818A06, 0xEC8177F83F900978, 0x190E714FADA5156E,
        0xB592BF39B0364963, 0x89C350C893AE7DC1, 0xAC042E70F8B383F2,
        0xB49B52E587A1EE60, 0xFB152FE3FF26DA89, 0x3E666E6F69AE2C15,
        0x3B544EBE544C19F9, 0xE805A1E290CF2456, 0x24B33C9D7ED25117,
        0xE74733427B72F0C1, 0x0A804D18B7097475, 0x57E3306D881EDB4F,
        0x4AE7D6A36EB5DBCB, 0x2D8D5432157064C8, 0xD1E649DE1E7F268B,
        0x8A328A1CEDFE552C, 0x07A3AEC79624C7DA, 0x84547DDC3E203C94,
        0x990A98FD5071D263, 0x1A4FF12616EEFC89, 0xF6F7FD1431714200,
        0x30C05B1BA332F41C, 0x8D2636B81555A786, 0x46C9FEB55D120902,
        0xCCEC0A73B49C9921, 0x4E9D2827355FC492, 0x19EBB029435DCB0F,
        0x4659D2B743848A2C, 0x963EF2C96B33BE31, 0x74F85198B05A2E7D,
        0x5A0F544DD2B1FB18, 0x03727073C2E134B1, 0xC7F6AA2DE59AEA61,
        0x352787BAA0D7C22F, 0x9853EAB63B5E0B35, 0xABBDCDD7ED5C0860,
        0xCF05DAF5AC8D77B0, 0x49CAD48CEBF4A71E, 0x7A4C10EC2158C4A6,
        0xD9E92AA246BF719E, 0x13AE978D09FE5557, 0x730499AF921549FF,
        0x4E4B705B92903BA4, 0xFF577222C14F0A3A, 0x55B6344CF97AAFAE,
        0xB862225B055B6960, 0xCAC09AFBDDD2CDB4, 0xDAF8E9829FE96B5F,
        0xB5FDFC5D3132C498, 0x310CB380DB6F7503, 0xE87FBB46217A360E,
        0x2102AE466EBB1148, 0xF8549E1A3AA5E00D, 0x07A69AFDCC42261A,
        0xC4C118BFE78FEAAE, 0xF9F4892ED96BD438, 0x1AF3DBE25D8F45DA,
        0xF5B4B0B0D2DEEEB4, 0x962ACEEFA82E1C84, 0x046E3ECAAF453CE9,
        0xF05D129681949A4C, 0x964781CE734B3C84, 0x9C2ED44081CE5FBD,
        0x522E23F3925E319E, 0x177E00F9FC32F791, 0x2BC60A63A6F3B3F2,
        0x222BBFAE61725606, 0x486289DDCC3D6780, 0x7DC7785B8EFDFC80,
        0x8AF38731C02BA980, 0x1FAB64EA29A2DDF7, 0xE4D9429322CD065A,
        0x9DA058C67844F20C, 0x24C0E332B70019B0, 0x233003B5A6CFE6AD,
        0xD586BD01C5C217F6, 0x5E5637885F29BC2B, 0x7EBA726D8C94094B,
        0x0A56A5F0BFE39272, 0xD79476A84EE20D06, 0x9E4C1269BAA4BF37,
        0x17EFEE45B0DEE640, 0x1D95B0A5FCF90BC6, 0x93CBE0B699C2585D,
        0x65FA4F227A2B6D79, 0xD5F9E858292504D5, 0xC2B5A03F71471A6F,
        0x59300222B4561E00, 0xCE2F8642CA0712DC, 0x7CA9723FBB2E8988,
        0x2785338347F2BA08, 0xC61BB3A141E50E8C, 0x150F361DAB9DEC26,
        0x9F6A419D382595F4, 0x64A53DC924FE7AC9, 0x142DE49FFF7A7C3D,
        0x0C335248857FA9E7, 0x0A9C32D5EAE45305, 0xE6C42178C4BBB92E,
        0x71F1CE2490D20B07, 0xF1BCC3D275AFE51A, 0xE728E8C83C334074,
        0x96FBF83A12884624, 0x81A1549FD6573DA5, 0x5FA7867CAF35E149,
        0x56986E2EF3ED091B, 0x917F1DD5F8886C61, 0xD20D8C88C8FFE65F,
        0x31D71DCE64B2C310, 0xF165B587DF898190, 0xA57E6339DD2CF3A0,
        0x1EF6E6DBB1961EC9, 0x70CC73D90BC26E24, 0xE21A6B35DF0C3AD7,
        0x003A93D8B2806962, 0x1C99DED33CB890A1, 0xCF3145DE0ADD4289,
        0xD0E4427A5514FB72, 0x77C621CC9FB3A483, 0x67A34DAC4356550B,
        0xF8D626AAAF278509)

    def __init__(self, random_array):
        self.random_array = random_array

    @property
    def random_array(self):
        """The tuple of 781 random 64 bit integers used by the hasher."""
        return self.__random_array

    @random_array.setter
    def random_array(self, value):
        if len(value) < 781:
            raise ValueError(
                "Expected at least 781 random numbers, got: %d." % len(value))

        self.__random_array = value

    def hash_position(self, position):
        """Computes the Zobrist hash of a position.

        :param position:
            The position to hash.

        :return:
            The hash as an integer.
        """
        key = 0

        # Hash in the board setup.
        for x in range(0, 8):
            for y in range(0, 8):
                piece = position[Square.from_x_and_y(x, y)]
                if piece:
                    i = "pPnNbBrRqQkK".index(piece.symbol)
                    key ^= self.__random_array[64 * i + 8 * y + x]

        # Hash in the castling flags.
        if position.get_castling_right("K"):
            key ^= self.__random_array[768]
        if position.get_castling_right("Q"):
            key ^= self.__random_array[768 + 1]
        if position.get_castling_right("k"):
            key ^= self.__random_array[768 + 2]
        if position.get_castling_right("q"):
            key ^= self.__random_array[768 + 3]

        # Hash in the en-passant file.
        if (position.ep_file and
               position.get_theoretical_ep_right(position.ep_file)):
            i = ord(position.ep_file) - ord("a")
            key ^= self.__random_array[772 + i]

        # Hash in the turn.
        if position.turn == "w":
            key ^= self.__random_array[780]

        return key

    @classmethod
    def create_random(cls):
        """Generates a new random number array using the random module
        and creates a new ZobristHasher from it.

        Its up to the caller to seed the random number generator (or not).
        """
        return cls(tuple(random.randint(0, 2**64) for i in range(0, 781)))


class GameHeaderBag(collections.MutableMapping):
    """A glorified dictionary of game headers as used in PGNs.

    :param game:
        Defaults to `None`. If bound to a game, any value set for
        `"PlyCount"` is ignored and instead the real ply count of the
        game is the value.
        Aditionally the `"FEN"` header can not be modified if the game
        already contains a move.

    These headers are required by the PGN standard and can not be
    removed:

    `"Event`":
        The name of the tournament or match event. Default is `"?"`.
    `"Site`":
        The location of the event. Default is `"?"`.
    `"Date`":
        The starting date of the game. Defaults to `"????.??.??"`. Must
        be a valid date of the form YYYY.MM.DD. `"??"` can be used as a
        placeholder for unknown month or day. `"????"` can be used as a
        placeholder for an unknown year.
    `"Round`":
        The playing round ordinal of the game within the event. Must be
        digits only or `"?"`. Defaults to `"?"`.
    `"White`":
        The player of the white pieces. Defaults to `"?"`.
    `"Black`":
        The player of the black pieces. Defaults to `"?"`.
    `"Result`":
        Defaults to `"*"`. Other values are `"1-0"` (white won),
        `"0-1"` (black won) and `"1/2-1/2"` (drawn).

    These additional headers are known:

    `"Annotator"`:
        The person providing notes to the game.
    `"PlyCount"`:
        The total moves played. Must be digits only. If a `game`
        parameter is given any value set will be ignored and the real
        ply count of the game will be used as the value.
    `"TimeControl"`:
        For example `"40/7200:3600"` (moves per seconds : sudden death
        seconds). Validated to be of this form.
    `"Time"`:
        Time the game started as a valid HH:MM:SS string.
    `"Termination"`:
        Can be one of `"abandoned"`, `"adjudication"`, `"death"`,
        `"emergency"`, `"normal"`, `"rules infraction"`,
        `"time forfeit"` or `"unterminated"`.
    `"Mode"`:
        Can be `"OTB"` (over-the-board) or `"ICS"` (Internet chess
        server).
    `"FEN"`:
        The initial position if the board as a FEN. If a game parameter
        was given and the game already contains moves, this header can
        not be set. The header will be deleted when set to the standard
        chess start FEN.
    `"SetUp"`:
        Any value set is ignored. Instead the value is `"1"` is the
        `"FEN"` header is set. Otherwise this header does not exist.

    An arbitrary amount of other headers can be set. The capitalization
    of the first occurence of a new header is used to normalize all
    further occurences to it. Additional headers are not validated.

    >>> import chess
    >>> bag = chess.GameHeaderBag()
    >>> bag["Annotator"] = "Alekhine"
    >>> bag["annOTator"]
    'Alekhine'
    >>> del bag["Annotator"]
    >>> "Annotator" in bag
    False

    `KNOWN_HEADERS`:
        The known headers in the order they will appear (if set) when
        iterating over the keys.
    """

    __date_regex = re.compile(r"^(\?{4}|[0-9]{4})(\.(\?\?|[0-9]{2})\.(\?\?|[0-9]{2}))?$")
    __round_part_regex = re.compile(r"^(\?|-|[0-9]+)$")
    __time_control_regex = re.compile(r"^([0-9]+)\/([0-9]+):([0-9]+)$")
    __time_regex = re.compile(r"^([0-9]{2}):([0-9]{2}):([0-9]{2})$")

    KNOWN_HEADERS = [
        "Event", "Site", "Date", "Round", "White", "Black", "Result",
        "Annotator", "PlyCount", "TimeControl", "Time", "Termination", "Mode",
        "FEN", "SetUp"]

    def __init__(self, game=None):
        self.__game = game
        self.__headers = {
            "Event": "?",
            "Site": "?",
            "Date": "????.??.??",
            "Round": "?",
            "White": "?",
            "Black": "?",
            "Result": "*",
        }

    def __normalize_key(self, key):
        if not isinstance(key, str):
            raise TypeError(
                "Expected string for GameHeaderBag key, got: %s." % repr(key))
        for header in itertools.chain(GameHeaderBag.KNOWN_HEADERS,
                                      self.__headers):
            if header.lower() == key.lower():
                return header
        return key

    def __len__(self):
        i = 0
        for header in self:
            i += 1
        return i

    def __iter__(self):
        for known_header in GameHeaderBag.KNOWN_HEADERS:
            if known_header in self:
                yield known_header
        for header in self.__headers:
            if not header in GameHeaderBag.KNOWN_HEADERS:
                yield header

    def __getitem__(self, key):
        key = self.__normalize_key(key)
        if self.__game and key == "PlyCount":
            return self.__game.ply
        elif key == "SetUp":
            return "1" if "FEN" in self else "0"
        elif key in self.__headers:
            return self.__headers[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        key = self.__normalize_key(key)
        if not isinstance(value, str):
            raise TypeError(
                "Expected value to be a string, got: %s." % repr(value))

        if key == "Date":
            matches = GameHeaderBag.__date_regex.match(value)
            if not matches:
                raise ValueError(
                    "Invalid value for Date header: %s." % repr(value))
            if not matches.group(2):
                value = "%s.??.??" % matches.group(1)
            else:
                year = matches.group(1) if matches.group(1) != "????" else "2000"
                month = int(matches.group(3)) if matches.group(3) != "??" else "10"
                day = int(matches.group(4)) if matches.group(4) != "??" else "1"
                datetime.date(int(year), int(month), int(day))
        elif key == "Round":
            parts = value.split(".")
            for part in parts:
                if not GameHeaderBag.__round_part_regex.match(part):
                    raise ValueError("Invalid value for Round header: %s." % repr(value))
        elif key == "Result":
            if not value in ["1-0", "0-1", "1/2-1/2", "*"]:
                raise ValueError(
                    "Invalid value for Result header: %s." % repr(value))
        elif key == "PlyCount":
            if not value.isdigit():
                raise ValueError(
                    "Invalid value for PlyCount header: %s." % repr(value))
            else:
                value = str(int(value))
        elif key == "TimeControl":
            pass
            # TODO: Implement correct parsing.
            #if not GameHeaderBag.__time_control_regex.match(value):
            #    raise ValueError(
            #        "Invalid value for TimeControl header: %s." % repr(value))
        elif key == "Time":
            matches = GameHeaderBag.__time_regex.match(value)
            if (not matches or
                int(matches.group(1)) < 0 or int(matches.group(1)) >= 24 or
                int(matches.group(2)) < 0 or int(matches.group(2)) >= 60 or
                int(matches.group(3)) < 0 or int(matches.group(3)) >= 60):
                raise ValueError(
                    "Invalid value for Time header: %s." % repr(value))
        elif key == "Termination":
            value = value.lower()

            # Support chess.com PGN files.
            if value.endswith(" won by resignation"):
                value = "normal"
            elif value.endswith(" drawn by repetition"):
                value = "normal"
            elif value.endswith(" won by checkmate"):
                value = "normal"
            elif value.endswith(" game abandoned"):
                value = "abandoned"

            # Ensure value matches the PGN standard.
            if not value in ["abandoned", "adjudication", "death", "emergency",
                             "normal", "rules infraction", "time forfeit",
                             "unterminated"]:
                raise ValueError(
                    "Invalid value for Termination header: %s." % repr(value))
        elif key == "Mode":
            value = value.upper()
            if not value in ["OTB", "ICS"]:
                raise ValueError(
                    "Invalid value for Mode header: %s." % repr(value))
        elif key == "FEN":
            value = Position(value).fen

            if value == START_FEN:
                if not "FEN" in self:
                    return
            else:
                if "FEN" in self and self["FEN"] == value:
                    return

            if self.__game and self.__game.ply > 0:
                raise ValueError(
                    "FEN header can not be set, when there are already moves.")

            if value == START_FEN:
                del self["FEN"]
                del self["SetUp"]
                return
            else:
                self["SetUp"] = "1"

        self.__headers[key] = value

    def __delitem__(self, key):
        k = self.__normalize_key(key)
        if k in ["Event", "Site", "Date", "Round", "White", "Black", "Result"]:
            raise KeyError(
                "The %s key can not be deleted because it is required." % k)
        del self.__headers[k]

    def __contains__(self, key):
        key = self.__normalize_key(key)
        if self.__game and key == "PlyCount":
            return True
        elif key == "SetUp":
            return "FEN" in self
        else:
            return self.__normalize_key(key) in self.__headers


class EcoFileParser(object):

    __move_regex = re.compile(r"([0-9]+\.)?(.*)")

    ECO_STATE = 0
    NAME_STATE = 1
    MOVETEXT_STATE = 2

    def __init__(self, create_classification=True, create_lookup=True):
        self.classification = dict() if create_classification else None
        self.lookup = dict() if create_lookup else None

        self.current_state = EcoFileParser.ECO_STATE
        self.current_eco = None
        self.current_name = None
        self.current_position = None

        self.chunks = collections.deque()

    def tokenize(self, filename):
        handle = open(filename, "r")
        for line in handle:
            line = line.strip().decode("latin-1")
            if not line or line.startswith("#"):
                continue

            self.chunks += line.split()

    def read_chunk(self):
        chunk = self.chunks.popleft()

        if self.classification is None and self.lookup is None:
            return

        if self.current_state == EcoFileParser.ECO_STATE:
            self.current_eco = chunk[0:3]
            self.current_name = ""
            self.current_position = Position()
            self.current_state = EcoFileParser.NAME_STATE
        elif self.current_state == EcoFileParser.NAME_STATE:
            if chunk.startswith("\""):
                chunk = chunk[1:]
            if chunk.endswith("\""):
                chunk = chunk[:-1]
                self.current_state = EcoFileParser.MOVETEXT_STATE
            self.current_name = (self.current_name + " " + chunk).strip()
        elif self.current_state == EcoFileParser.MOVETEXT_STATE:
            if chunk == "*":
                self.current_state = EcoFileParser.ECO_STATE
                if not self.classification is None:
                    self.classification[hash(self.current_position)] = {
                        "eco": self.current_eco,
                        "name": self.current_name,
                        "fen": self.current_position.fen,
                    }
                if not self.lookup is None and not self.current_eco in self.lookup:
                    self.lookup[self.current_eco] = {
                        "name": self.current_name,
                        "fen": self.current_position.fen,
                    }
            else:
                if self.classification is not None or not self.current_eco in self.lookup:
                    match = EcoFileParser.__move_regex.match(chunk)
                    if match.group(2):
                        self.current_position.make_move(self.current_position.get_move_from_san(match.group(2)))

    def read_all(self):
        while self.chunks:
            self.read_chunk()
        assert self.current_state == EcoFileParser.ECO_STATE


class Board(QWidget):

    def __init__(self, parent):
        super(Board, self).__init__()
        self.margin = 0.1
        self.padding = 0.06
        self.showCoordinates = True
        self.lightSquareColor = QColor(255, 255, 255)
        self.darkSquareColor = QColor(100, 100, 255)
        self.borderColor = QColor(100, 100, 200)
        self.shadowWidth = 2
        self.rotation = 0
        self.ply = 1
        self.setWindowTitle('Chess')
        self.backgroundPixmap = QPixmap(plugin_super_class.path_to_data('chess') + "background.png")

        self.draggedSquare = None
        self.dragPosition = None

        self.position = Position()

        self.parent = parent

        # Load piece set.
        self.pieceRenderers = dict()
        for symbol in "PNBRQKpnbrqk":
            piece = Piece(symbol)
            self.pieceRenderers[piece] = QSvgRenderer(plugin_super_class.path_to_data('chess') + "classic-pieces/%s-%s.svg" % (piece.full_color, piece.full_type))

    def update_title(self):
        if self.position.is_checkmate():
            self.setWindowTitle('Checkmate')
        elif self.position.is_stalemate():
            self.setWindowTitle('Stalemate')

    def mousePressEvent(self, e):
        self.dragPosition = e.pos()
        square = self.squareAt(e.pos())
        if self.canDragSquare(square):
            self.draggedSquare = square

    def mouseMoveEvent(self, e):
        if self.draggedSquare:
            self.dragPosition = e.pos()
            self.repaint()

    def mouseReleaseEvent(self, e):
        if self.draggedSquare:
            dropSquare = self.squareAt(e.pos())
            if dropSquare == self.draggedSquare:
                self.onSquareClicked(self.draggedSquare)
            elif dropSquare:
                move = self.moveFromDragDrop(self.draggedSquare, dropSquare)
                if move:
                    self.position.make_move(move)
                    self.parent.move(move)
                    self.ply += 1
            self.draggedSquare = None
            self.repaint()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)

        # Light shines from upper left.
        if math.cos(math.radians(self.rotation)) >= 0:
            lightBorderColor = self.borderColor.lighter()
            darkBorderColor = self.borderColor.darker()
        else:
            lightBorderColor = self.borderColor.darker()
            darkBorderColor = self.borderColor.lighter()

        # Draw the background.
        backgroundBrush = QBrush(Qt.red, self.backgroundPixmap)
        backgroundBrush.setStyle(Qt.TexturePattern)
        painter.fillRect(QRect(QPoint(0, 0), self.size()), backgroundBrush)

        # Do the rotation.
        painter.save()
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.rotation)

        # Draw the border.
        frameSize = min(self.width(), self.height()) * (1 - self.margin * 2)
        borderSize = min(self.width(), self.height()) * self.padding
        painter.translate(-frameSize / 2, -frameSize / 2)
        painter.fillRect(QRect(0, 0, frameSize, frameSize), self.borderColor)
        painter.setPen(QPen(QBrush(lightBorderColor), self.shadowWidth))
        painter.drawLine(0, 0, 0, frameSize)
        painter.drawLine(0, 0, frameSize, 0)
        painter.setPen(QPen(QBrush(darkBorderColor), self.shadowWidth))
        painter.drawLine(frameSize, 0, frameSize, frameSize)
        painter.drawLine(0, frameSize, frameSize, frameSize)

        # Draw the squares.
        painter.translate(borderSize, borderSize)
        squareSize = (frameSize - 2 * borderSize) / 8.0
        for x in range(0, 8):
            for y in range(0, 8):
                rect = QRect(x * squareSize, y * squareSize, squareSize, squareSize)
                if (x - y) % 2 == 0:
                     painter.fillRect(rect, QBrush(self.lightSquareColor))
                else:
                     painter.fillRect(rect, QBrush(self.darkSquareColor))

        # Draw the inset.
        painter.setPen(QPen(QBrush(darkBorderColor), self.shadowWidth))
        painter.drawLine(0, 0, 0, squareSize * 8)
        painter.drawLine(0, 0, squareSize * 8, 0)
        painter.setPen(QPen(QBrush(lightBorderColor), self.shadowWidth))
        painter.drawLine(squareSize * 8, 0, squareSize * 8, squareSize * 8)
        painter.drawLine(0, squareSize * 8, squareSize * 8, squareSize * 8)

        # Display coordinates.
        if self.showCoordinates:
            painter.setPen(QPen(QBrush(self.borderColor.lighter()), self.shadowWidth))
            coordinateSize = min(borderSize, squareSize)
            font = QFont()
            font.setPixelSize(coordinateSize * 0.6)
            painter.setFont(font)
            for i, rank in enumerate(["8", "7", "6", "5", "4", "3", "2", "1"]):
                pos = QRect(-borderSize, squareSize * i, borderSize, squareSize).center()
                painter.save()
                painter.translate(pos.x(), pos.y())
                painter.rotate(-self.rotation)
                painter.drawText(QRect(-coordinateSize / 2, -coordinateSize / 2, coordinateSize, coordinateSize), Qt.AlignCenter, rank)
                painter.restore()
            for i, file in enumerate(["a", "b", "c", "d", "e", "f", "g", "h"]):
                pos = QRect(squareSize * i, squareSize * 8, squareSize, borderSize).center()
                painter.save()
                painter.translate(pos.x(), pos.y())
                painter.rotate(-self.rotation)
                painter.drawText(QRect(-coordinateSize / 2, -coordinateSize / 2, coordinateSize, coordinateSize), Qt.AlignCenter, file)
                painter.restore()

        # Draw pieces.
        for x in range(0, 8):
            for y in range(0, 8):
                square = Square.from_x_and_y(x, 7 - y)
                piece = self.position[square]
                if piece and square != self.draggedSquare:
                    painter.save()
                    painter.translate((x + 0.5) * squareSize, (y + 0.5) * squareSize)
                    painter.rotate(-self.rotation)
                    self.pieceRenderers[piece].render(painter, QRect(-squareSize / 2, -squareSize / 2, squareSize, squareSize))
                    painter.restore()

        # Draw a floating piece.
        painter.restore()
        if self.draggedSquare:
            piece = self.position[self.draggedSquare]
            if piece:
                painter.save()
                painter.translate(self.dragPosition.x(), self.dragPosition.y())
                painter.rotate(-self.rotation)
                self.pieceRenderers[piece].render(painter, QRect(-squareSize / 2, -squareSize / 2, squareSize, squareSize))
                painter.restore()

        painter.end()

    def squareAt(self, point):
        # Undo the rotation.
        transform = QTransform()
        transform.translate(self.width() / 2, self.height() / 2)
        transform.rotate(self.rotation)
        logicalPoint = transform.inverted()[0].map(point)

        frameSize = min(self.width(), self.height()) * (1 - self.margin * 2)
        borderSize = min(self.width(), self.height()) * self.padding
        squareSize = (frameSize - 2 * borderSize) / 8.0
        x = int(logicalPoint.x() / squareSize + 4)
        y = 7 - int(logicalPoint.y() / squareSize + 4)
        try:
            return Square.from_x_and_y(x, y)
        except IndexError:
            return None

    def canDragSquare(self, square):
        if (self.ply % 2 == 0 and self.parent.white) or (self.ply % 2 == 1 and not self.parent.white):
            return False
        for move in self.position.get_legal_moves():
            if move.source == square:
                return True
        return False

    def onSquareClicked(self, square):
        pass

    def moveFromDragDrop(self, source, target):
        for move in self.position.get_legal_moves():
            if move.source == source and move.target == target:
                if move.promotion:
                    dialog = PromotionDialog(self.position[move.source].color, self)
                    if dialog.exec_():
                        return Move(source, target, dialog.selectedType())
                else:
                    return move
                return move


class PromotionDialog(QDialog):

    def __init__(self, color, parent=None):
        super(PromotionDialog, self).__init__(parent)

        self.promotionTypes = ["q", "n", "r", "b"]

        grid = QGridLayout()
        hbox = QHBoxLayout()
        grid.addLayout(hbox, 0, 0)

        # Add the piece buttons.
        self.buttonGroup = QButtonGroup(self)
        for i, promotionType in enumerate(self.promotionTypes):
            # Create an icon for the piece.
            piece = Piece.from_color_and_type(color, promotionType)
            renderer = QSvgRenderer(plugin_super_class.path_to_data('chess') + "classic-pieces/%s-%s.svg" % (piece.full_color, piece.full_type))
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.transparent)
            painter = QPainter()
            painter.begin(pixmap)
            renderer.render(painter, QRect(0, 0, 32, 32))
            painter.end()

            # Add the button.
            button = QPushButton(QIcon(pixmap), '', self)
            button.setCheckable(True)
            self.buttonGroup.addButton(button, i)
            hbox.addWidget(button)

        self.buttonGroup.button(0).setChecked(True)

        # Add the ok and cancel buttons.
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        grid.addWidget(buttons, 1, 0)

        self.setLayout(grid)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    def selectedType(self):
        return self.promotionTypes[self.buttonGroup.checkedId()]


class Chess(plugin_super_class.PluginSuperClass):

    def __init__(self, *args):
        super(Chess, self).__init__('Chess', 'chess', *args)
        self.game = -1
        self.board = None
        self.white = True
        self.pre = None

    def get_description(self):
        return QApplication.translate("Chess", 'Plugin which allows you to play chess with your friends.', None, QApplication.UnicodeUTF8)

    def lossless_packet(self, data, friend_number):
        print('data ' + data)
        if data == 'new':
            self.pre = None
            reply = QMessageBox.question(None,
                                               'New game',
                                               'New game',
                                               QMessageBox.Yes,
                                               QMessageBox.No)
            if reply != QMessageBox.Yes:
                self.send_lossless('no', friend_number)
            else:
                self.send_lossless('yes', friend_number)
                self.board = Board(self)
                self.board.show()
                self.game = friend_number
                self.white = False
        elif data == 'yes' and friend_number == self.game:
            self.board = Board(self)
            self.board.show()
        elif data == 'no':
            self.game = -1
        else:  # move
            if data != self.pre:
                self.pre = data
                a = Square.from_x_and_y(ord(data[0]) - ord('a'), ord(data[1]) - ord('1'))
                b = Square.from_x_and_y(ord(data[2]) - ord('a'), ord(data[3]) - ord('1'))
                self.board.position.make_move(Move(a, b, data[4] if len(data) == 5 else None))
                self.board.update_title()
                self.board.ply += 1

    def start_game(self, num):
        self.white = True
        self.send_lossless('new', num)
        self.game = num

    def move(self, move):
        self.send_lossless(str(move), self.game)
        self.board.update_title()

    def get_menu(self, menu, num):
        act = QAction(QApplication.translate("TOXID", "Start game", None, QApplication.UnicodeUTF8), menu)
        act.connect(act, SIGNAL("triggered()"), lambda: self.start_game(num))
        return [act]
