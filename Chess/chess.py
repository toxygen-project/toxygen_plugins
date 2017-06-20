# -*- coding: utf-8 -*-

import collections
import re
import math
import plugin_super_class

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import *


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

    def update_title(self, my_move=False):
        if self.position.is_checkmate():
            self.setWindowTitle('Checkmate')
        elif self.position.is_stalemate():
            self.setWindowTitle('Stalemate')
        else:
            self.setWindowTitle('Chess' + (' [Your move]' if my_move else ''))

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

    def closeEvent(self, *args):
        self.parent.stop_game()

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
        self.last_move = None
        self.is_my_move = False

    def get_description(self):
        return QApplication.translate("Chess", 'Plugin which allows you to play chess with your friends.', None, QApplication.UnicodeUTF8)

    def lossless_packet(self, data, friend_number):
        if data == 'new':
            self.pre = None
            friend = self._profile.get_friend_by_number(friend_number)
            reply = QMessageBox.question(None,
                                         'New chess game',
                                         'Friend {} wants to play chess game against you. Start?'.format(friend.name),
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
                self.is_my_move = False
        elif data == 'yes' and friend_number == self.game:
            self.board = Board(self)
            self.board.show()
            self.board.update_title(True)
            self.is_my_move = True
            self.last_move = None
        elif data == 'no':
            self.game = -1
        elif data != self.pre:  # move
            self.pre = data
            self.is_my_move = True
            self.last_move = None
            a = Square.from_x_and_y(ord(data[0]) - ord('a'), ord(data[1]) - ord('1'))
            b = Square.from_x_and_y(ord(data[2]) - ord('a'), ord(data[3]) - ord('1'))
            self.board.position.make_move(Move(a, b, data[4] if len(data) == 5 else None))
            self.board.repaint()
            self.board.update_title(True)
            self.board.ply += 1

    def start_game(self, num):
        self.white = True
        self.send_lossless('new', num)
        self.game = num

    def resend_move(self):
        if self.is_my_move or self.last_move is None:
            return
        self.send_lossless(str(self.last_move), self.game)
        QTimer.singleShot(1000, self.resend_move)

    def stop_game(self):
        self.last_move = None

    def move(self, move):
        self.is_my_move = False
        self.last_move = move
        self.send_lossless(str(move), self.game)
        self.board.update_title()
        QTimer.singleShot(1000, self.resend_move)

    def get_menu(self, menu, num):
        act = QAction(QApplication.translate("Chess", "Start chess game", None, QApplication.UnicodeUTF8), menu)
        act.triggered.connect(lambda: self.start_game(num))
        return [act]
