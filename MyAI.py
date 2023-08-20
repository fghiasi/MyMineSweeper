# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Farbod Ghiasi
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================


# TODO: PUT the comment back for imports and AI in MyAI(argument)
# TODO: AI in myAI class 2- imports are changed
# from Minesweeper_Python.src.AI import AI
# from Minesweeper_Python.src.Action import Action

from AI import AI
from Action import Action


class MyAI(AI):

    ########################################################################
    #							YOUR CODE BEGINS						   #
    ########################################################################

    def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
        self.__action = AI.Action.UNCOVER
        self.__move_count = 1
        self.__rowDimension = rowDimension
        self.__colDimension = colDimension
        self._total_covered_tiles = rowDimension * colDimension
        self._total_board_tiles = rowDimension * colDimension
        self.__total_given_mines = totalMines
        self.__remained_mines = totalMines
        self.__start_x = startX
        self.__start_y = startY
        self.__tile = (startY, startX)

        self.total_csp_solutions = 0
        self.stat_dict = dict()

        self.__frontier = []

        # safe moves from frontier # later it must use more than just frontier
        self.__safe_moves = []

        self.__board = self.Board(rowDimension, colDimension, totalMines)
        self.board = self.__board
    ########################################################################
    #							YOUR CODE ENDS							   #
    ########################################################################

    def getAction(self, number: int) -> "Action Object":
        # print("_total_board_tiles",self._total_board_tiles, "_remained_mines ", self.__remained_mines,
        #       " _total_covered_tiles: ", self._total_covered_tiles)

        ########################################################################
        #							YOUR CODE BEGINS						   #
        ########################################################################

        if self._total_covered_tiles == self.__total_given_mines:
            print("WON!")
            return Action(AI.Action.LEAVE)

        self.update(self.__tile, number)
        self.__safe_moves = self.find_safe_moves()
        if not self.__safe_moves:
            self.__safe_moves, mine_tiles = self.group_model_safe_tiles()
            if not self.__safe_moves and mine_tiles:
                self.__safe_moves = self.find_safe_moves()
        if not self.__safe_moves:
            self.__safe_moves = []
            covered_frontier, uncovered_frontier = self.find_frontier()

            if len(covered_frontier) < 20:
                # print("covered_frontier len running BT", len(covered_frontier))
                self.total_csp_solutions = 0
                self.stat_dict = dict()
                self.csp_backtrack(covered_frontier, uncovered_frontier, [])
                # if not self.stat_dict:
                    # print("usless stat dict is empty")
                for tile in self.stat_dict:
                    # print("tile: ", tile, " is ", (self.stat_dict[tile] / self.total_csp_solutions), " likely to be a mine.")
                    if (self.stat_dict[tile] / self.total_csp_solutions) > 0.85:
                        if self.is_valid_to_flag(tile):
                            # print("flagging ", tile)
                            self.flag_one_tile(tile)
                    if 0.0001 < (self.stat_dict[tile] / self.total_csp_solutions) < 0.126:
                        # print("safe tiles appended ", tile)
                        self.__safe_moves.append(tile)
                # print("safe moves found after flagging: ", self.__safe_moves)
                self.__safe_moves, mine_tiles = self.group_model_safe_tiles()
                if not self.__safe_moves and mine_tiles:
                    self.__safe_moves = self.find_safe_moves()
        if not self.__safe_moves:
            for tile in self.stat_dict:
                if (self.stat_dict[tile] / self.total_csp_solutions) < 0.210:
                    self.__safe_moves.append(tile)
        if not self.__safe_moves:
            for tile in self.stat_dict:
                if (self.stat_dict[tile] / self.total_csp_solutions) < 0.29:
                    self.__safe_moves.append(tile)

        if not self.__safe_moves:
            for tile in self.stat_dict:
                if (self.stat_dict[tile] / self.total_csp_solutions) < 0.49:
                    self.__safe_moves.append(tile)

        if not self.__safe_moves:
            # print("still random!=================================================================== ")
            # print("still random!=================================================================== ")
            # print("still random!=================================================================== ")
            # print("still random!=================================================================== ")

            covered_tiles = self.__board.all_covered_tiles()
            self.__safe_moves = covered_tiles

        if not self.__safe_moves or self._total_covered_tiles == self.__total_given_mines:
            print("LOST/WON")
            return Action(AI.Action.LEAVE)

        safe_move = self.pop_tile_from_safe_moves()
        row, col = safe_move
        self.__tile = (row, col)

        return Action(self.__action, col, row)

    ########################################################################
    #							YOUR CODE ENDS							   #
    ########################################################################

    def update(self, tile, mine_count):
        tile = self.__board.is_tile_in_bound(tile)
        self.increment_move_count()
        self.__board.assign_tile_mine_count(tile, mine_count)
        self._total_covered_tiles -= 1

    def find_safe_moves(self):
        if self.move_count() == 1:
            return [(self.__start_y, self.__start_x)]

        self.flag_tiles_with_mine()

        safe_neighbours = self.find_tiles_with_zero_mine_neighbour()
        return safe_neighbours

    def find_frontier(self):
        uncovered_frontier = self.uncovered_frontier()
        covered_frontier = self.covered_frontier(uncovered_frontier)
        return covered_frontier, uncovered_frontier

    def covered_frontier(self, uncovered_frontier):
        covered_frontier = []
        for uncovered_tile in uncovered_frontier:
            tile_covered_neighbours = self.__board.tile_covered_neighbours(uncovered_tile)
            covered_neighbours = [covered_tile for covered_tile
                                  in tile_covered_neighbours
                                  if covered_tile not in covered_frontier]
            covered_frontier.extend(covered_neighbours)
        return covered_frontier

    def uncovered_frontier(self):
        uncovered_frontier = []
        all_covered_tiles = self.__board.all_covered_tiles()
        for covered_tile in all_covered_tiles:
            tile_uncovered_neighbours = self.__board.tile_uncovered_neighbours(covered_tile)
            uncovered_neighbours = [uncovered_tile for uncovered_tile
                                    in tile_uncovered_neighbours
                                    if covered_tile not in uncovered_frontier]
            uncovered_frontier.extend(uncovered_neighbours)
        return list(set(uncovered_frontier))

    def group_model_safe_tiles(self):
        _, uncovered_frontier = self.find_frontier()
        mine_tiles, safe_tiles = self.model_check_uncovered_frontier_tiles(uncovered_frontier)
        if mine_tiles:
            self.flag_tiles(mine_tiles)
        return safe_tiles, mine_tiles

    def model_check_uncovered_frontier_tiles(self, uncovered_frontier):
        mine_tiles = []
        safe_tiles = []
        for covered_group_root_tile in uncovered_frontier:
            covered_group_tiles = self.__board.tile_covered_neighbours(covered_group_root_tile)
            uncovered_group_tiles = self.covered_group_uncovered_neighbours(covered_group_root_tile,
                                                                            covered_group_tiles)
            mine_tiles_tmp, safe_tiles_tmp = self.model_check(covered_group_root_tile, uncovered_group_tiles,
                                                              covered_group_tiles)
            mine_tiles.extend(mine_tiles_tmp)
            safe_tiles.extend(safe_tiles_tmp)
        return list(set(mine_tiles)), list(set(safe_tiles))

    def model_check(self, covered_group_root_tile, uncovered_group_tiles, covered_group_tiles):
        mine_tiles = []
        safe_tiles = []
        for uncovered_group_selected_tile in uncovered_group_tiles:
            mine_tiles_tmp, safe_tiles_tmp = self.model_check_one_uncovered_tile(covered_group_root_tile,
                                                                                 covered_group_tiles,
                                                                                 uncovered_group_selected_tile)
            mine_tiles.extend(mine_tiles_tmp)
            safe_tiles.extend(safe_tiles_tmp)

        return mine_tiles, safe_tiles

    def model_check_one_uncovered_tile(self, covered_group_root_tile, covered_group_tiles,
                                       uncovered_group_selected_tile):
        selected_tile_covered_neighbours = self.__board.tile_covered_neighbours(uncovered_group_selected_tile)
        selected_tile_shared_tiles_with_covered_group = [tile for tile
                                                         in selected_tile_covered_neighbours
                                                         if tile in covered_group_tiles]
        selected_tile_uncommon_tiles_with_covered_group = [tile for tile
                                                           in selected_tile_covered_neighbours
                                                           if tile not in covered_group_tiles]

        mine_tiles, safe_tiles = self.infer_safe_or_mine_tiles(covered_group_root_tile, covered_group_tiles,
                                                               uncovered_group_selected_tile,
                                                               selected_tile_uncommon_tiles_with_covered_group,
                                                               selected_tile_shared_tiles_with_covered_group)

        return mine_tiles, safe_tiles

    def infer_safe_or_mine_tiles(self, covered_group_root_tile, covered_group_tiles, selected_uncovered_tile,
                                 selected_tile_uncommon_tiles_with_covered_group,
                                 selected_tile_shared_tiles_with_covered_group):
        safe_tiles = []
        mine_tiles = []
        covered_group_mine_count = self.__board.tile_mine_count(covered_group_root_tile)
        uncommon_covered_tiles = selected_tile_uncommon_tiles_with_covered_group
        uncommon_covered_tiles_count = len(uncommon_covered_tiles)
        shared_covered_tiles_count = len(selected_tile_shared_tiles_with_covered_group)
        covered_group_tiles_count = len(covered_group_tiles)
        selected_uncovered_tile_mine_count = self.__board.tile_mine_count(selected_uncovered_tile)
        covered_group_safe_tiles_count = covered_group_tiles_count - covered_group_mine_count

        if selected_uncovered_tile_mine_count == 0:
            # print("selected_tile_shared_tiles_with_covered_group : ", selected_tile_shared_tiles_with_covered_group)
            # print("uncommon_covered_tiles : ", uncommon_covered_tiles)
            safe_tiles.extend(selected_tile_shared_tiles_with_covered_group)
            safe_tiles.extend(uncommon_covered_tiles)

        if covered_group_mine_count == 0:
            # print("covered_group_tiles : ", covered_group_tiles)
            safe_tiles.extend(covered_group_tiles)

        if covered_group_mine_count == covered_group_tiles_count:
            mine_tiles.extend(covered_group_tiles)

        if selected_uncovered_tile_mine_count == (uncommon_covered_tiles_count + shared_covered_tiles_count):
            mine_tiles.extend(selected_tile_shared_tiles_with_covered_group)
            mine_tiles.extend(uncommon_covered_tiles)

        if shared_covered_tiles_count > covered_group_safe_tiles_count:
            shared_covered_tiles_mine_count = shared_covered_tiles_count - covered_group_safe_tiles_count
            selected_tile_new_mine_count = selected_uncovered_tile_mine_count - shared_covered_tiles_mine_count
            if selected_tile_new_mine_count == 0:
                safe_tiles.extend(uncommon_covered_tiles)
            elif uncommon_covered_tiles_count == selected_tile_new_mine_count and shared_covered_tiles_count - \
                    selected_tile_new_mine_count == 0:
                mine_tiles.extend(uncommon_covered_tiles)

        if shared_covered_tiles_count > covered_group_mine_count:
            shared_covered_tiles_max_mines = covered_group_mine_count
        else:
            shared_covered_tiles_max_mines = shared_covered_tiles_count

        if selected_uncovered_tile_mine_count > shared_covered_tiles_max_mines:
            remained_mines = selected_uncovered_tile_mine_count - shared_covered_tiles_max_mines
            if uncommon_covered_tiles_count == remained_mines:
                mine_tiles.extend(uncommon_covered_tiles)

        return mine_tiles, safe_tiles

    def csp_backtrack(self, covered_frontier, uncovered_frontier, r):
        for index1, covered_tile1 in enumerate(covered_frontier):
            if self.is_valid_to_flag(covered_tile1):
                self.flag_one_tile(covered_tile1)
                r.append(covered_tile1)
                self.csp_backtrack(covered_frontier[index1+1:], uncovered_frontier, r)
                self.unflagg_one_tile(covered_tile1)
                r.remove(covered_tile1)
        if self.csp_satisfied(uncovered_frontier):
            # print(r)
            self.stat(r)
        return

    def csp_satisfied(self, uncovered_frontier):
        for uncovered_tile in uncovered_frontier:
            if self.__board.tile_mine_count(uncovered_tile) != 0:
                return False
        return True

    def stat(self, r):
        self.total_csp_solutions += 1
        for tile in r:
            if tile not in self.stat_dict:
                self.stat_dict[tile] = 1
            else:
                self.stat_dict[tile] += 1

    def is_valid_to_flag(self, tile):
        if not self.__board.is_tile_covered(tile) or self.__board.is_tile_flagged(tile):
            return False
        tile_uncovered_neighbours = self.__board.tile_uncovered_neighbours(tile)
        for uncovered_tile in tile_uncovered_neighbours:
            tile_mine_count = self.__board.tile_mine_count(uncovered_tile)
            if tile_mine_count == 0:
                return False
        return True

    def unflagg_one_tile(self, tile):
        self.__board.unflagg_tile(tile)
        self.increment_remained_mines()

    def flag_one_tile(self, tile):
        self.__board.flag_tile(tile)
        self.decrement_remained_mines()

    def covered_group_uncovered_neighbours(self, covered_group_root_tile, covered_group):
        uncovered_group = []
        for covered_tile in covered_group:
            tile_uncovered_neighbours = self.__board.tile_uncovered_neighbours(covered_tile)
            tile_uncovered_neighbours = [tile for tile
                                         in tile_uncovered_neighbours
                                         if tile != covered_group_root_tile
                                         and tile not in uncovered_group]
            uncovered_group.extend(tile_uncovered_neighbours)
        return uncovered_group

    def find_tiles_with_zero_mine_neighbour(self):
        uncovered_tiles = self.__board.find_all_uncovered_tiles()

        for uncovered_tile in uncovered_tiles:
            if self.__board.tile_mine_count(uncovered_tile) == 0:
                covered_tile_neighbours = self.__board.tile_covered_neighbours(uncovered_tile)
                self.__safe_moves.extend(covered_tile_neighbours)
        self.__safe_moves = [t for t in (set(i for i in self.__safe_moves))]

        return self.__safe_moves

    def flag_tiles_with_mine(self):
        # TODO: needs pruning we don't have to get all uncovered tiles if their neighbours are all
        # TODO : uncovered
        uncovered_tiles = self.__board.find_all_uncovered_tiles()
        for uncovered_tile in uncovered_tiles:
            tile_mine_count = self.__board.tile_mine_count(uncovered_tile)
            tile_covered_tiles_count = self.__board.get_tile_covered_neighbours_count(uncovered_tile)
            if tile_mine_count == tile_covered_tiles_count:
                tile_covered_tiles = self.__board.tile_covered_neighbours(uncovered_tile)
                self.flag_tiles(tile_covered_tiles)

    def flag_tiles(self, tiles):
        for tile in tiles:
            self.__board.flag_tile(tile)
            self.__remained_mines -= 1

    def decrement_remained_mines(self):
        self.__remained_mines -= 1

    def increment_remained_mines(self):
        self.__remained_mines += 1

    def pop_tile_from_safe_moves(self):
        return self.__safe_moves.pop()

    def remove_tile_from_safe_moves(self, tile):
        return self.__safe_moves.remove(tile)

    def get_remained_mines(self):
        return self.__remained_mines
    
    def increment_move_count(self):
        self.__move_count += 1

    def move_count(self):
        return self.__move_count

    ########################################################################
    #				  MYAI CLASS UTILITY FUNCTIONS BEGINS				   #
    ########################################################################

    ########################################################################
    #				   MYAI CLASS UTILITY FUNCTIONS ENDS				   #
    ########################################################################

    ########################################################################
    #							BOARD CLASS BEGINS						   #
    ########################################################################

    class Board:

        def __init__(self, row_dimension, column_dimension, total_mines):
            # TODO: assign probability to each tile and use it for random choosing
            # it should be based on mines left and frontier that has
            # tiles with mine values
            self._row_dimension = row_dimension - 1
            self._column_dimension = column_dimension - 1
            self._total_mines = total_mines
            self._total_covered_tiles = row_dimension * column_dimension
            self._remaining_mines = total_mines
            self._move_count = 0
            self._flagged_tile_covered_neighbours = dict()

            self._board = self.init_board()

        def init_board(self):
            board = []
            for i in range(self._row_dimension + 1):
                col = []
                for j in range(self._column_dimension + 1):
                    col.append({"covered": True, "flagged": False, "mine_count": None})
                board.append(col)
            return board

        def assign_tile_mine_count(self, tile, mine_count):

            tile, mine_count = self.is_valid_mine_count(tile, mine_count)
            row, col = self.is_tile_in_bound(tile)
            self._total_covered_tiles -= 1
            self.uncover_tile(tile)
            if self._board[row][col]["mine_count"]:
                self._board[row][col]["mine_count"] += mine_count
            else:
                self._board[row][col]["mine_count"] = mine_count

        def tile_mine_count(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return self._board[row][col]["mine_count"]

        def increment_tile_neighbours_mine_count(self, tile):
            tile_neighbours = self.tile_neighbours(tile)
            for tile_neighbour in tile_neighbours:
                row, col = tile_neighbour
                if self._board[row][col]["mine_count"] == -1:
                    self._board[row][col]["mine_count"] = None
                else:
                    self._board[row][col]["mine_count"] += 1

        def decrement_tile_neighbours_mine_count(self, tile):
            self.is_tile_in_bound(tile)
            tile_neighbours = self.tile_neighbours(tile)
            for tile_neighbour in tile_neighbours:
                row, col = tile_neighbour
                if self._board[row][col]["mine_count"]:
                    self._board[row][col]["mine_count"] -= 1
                else:
                    self._board[row][col]["mine_count"] = -1

        def unflagg_tile(self, tile):
            tile = self.is_valid_to_unflagg(tile)
            tile = self.is_tile_in_bound(tile)
            row, col = tile

            self._board[row][col]["flagged"] = False
            self._board[row][col]["covered"] = True
            self._remaining_mines += 1
            self._total_covered_tiles += 1

            self.increment_tile_neighbours_mine_count(tile)

        def flag_tile(self, tile):
            tile = self.is_valid_to_flag(tile)
            tile = self.is_tile_in_bound(tile)
            row, col = tile

            self._board[row][col]["flagged"] = True
            self._board[row][col]["covered"] = False
            self._remaining_mines -= 1
            self._total_covered_tiles -= 1

            self.decrement_tile_neighbours_mine_count(tile)

        def find_tile_flagged_tiles(self, tile):
            tile = self.is_tile_in_bound(tile)
            flagged_tiles = []
            tile_neighbours = self.tile_neighbours(tile)
            for tile in tile_neighbours:
                row, col = tile
                if self._board[row][col]["flagged"]:
                    flagged_tiles.append((row, col))
            return flagged_tiles

        def get_all_covered_flagged_neighbours(self):
            return self._flagged_tile_covered_neighbours

        def all_covered_tiles(self):
            covered_tiles = []
            for row in range(self._row_dimension + 1):
                for col in range(self._column_dimension + 1):
                    if self._board[row][col]["covered"]:
                        covered_tiles.append((row, col))
            return covered_tiles

        def find_all_uncovered_tiles(self):
            uncovered_tiles = []
            for row in range(self._row_dimension + 1):
                for col in range(self._column_dimension + 1):
                    if not self._board[row][col]["covered"]:
                        uncovered_tiles.append((row, col))
            return uncovered_tiles

        def get_all_covered_tiles_count(self):
            return len(self.all_covered_tiles())

        def get_all_uncovered_tiles_count(self):
            return len(self.find_all_uncovered_tiles())

        def uncover_tile(self, tile):
            tile = self.is_tile_in_bound(tile)
            row, col = tile
            self._board[row][col]["covered"] = False

        def tile_covered_neighbours(self, tile):
            tile = self.is_tile_in_bound(tile)

            tile_neighbours = self.tile_neighbours(tile)

            covered_tile_neighbours = []

            for tile in tile_neighbours:
                if self.is_tile_covered(tile):
                    covered_tile_neighbours.append(tile)
            return covered_tile_neighbours

        def tile_uncovered_neighbours(self, tile):
            tile = self.is_tile_in_bound(tile)

            tile_neighbours = self.tile_neighbours(tile)

            uncovered_neighbours = []

            for tile in tile_neighbours:
                if not self.is_tile_covered(tile) and not self.is_tile_flagged(tile):
                    uncovered_neighbours.append(tile)
            return uncovered_neighbours

        def get_tile_covered_neighbours_count(self, tile):

            return len(self.tile_covered_neighbours(tile))

        def get_tile_uncovered_neighbours_count(self, tile):

            return len(self.tile_uncovered_neighbours(tile))

        def tile_neighbours(self, tile):
            tile = self.is_tile_in_bound(tile)
            if self.is_tile_adjacent_to_wall(tile):
                return self.wall_adjacent_neighbours(tile)
            else:
                return self.tile_eight_neighbours(tile)

        def tile_eight_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return [
                (row + 1, col),
                (row + 1, col + 1),
                (row + 1, col - 1),

                (row, col - 1),
                (row, col + 1),

                (row - 1, col),
                (row - 1, col + 1),
                (row - 1, col - 1)

            ]

        def is_tile_flagged(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return self._board[row][col]["flagged"]

        def is_tile_covered(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return self._board[row][col]["covered"]

        def is_tile_adjacent_to_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            if row == 0 or col == 0 or \
                    row == self._row_dimension or col == self._column_dimension:
                return True
            return False

        def wall_adjacent_neighbours(self, tile):
            if self.is_tile_in_north_wall(tile):
                return self.tile_north_wall_neighbours(tile)

            if self.is_tile_in_south_wall(tile):
                return self.tile_south_wall_neighbours(tile)

            if self.is_tile_in_east_wall(tile):
                return self.tile_east_wall_neighbours(tile)

            if self.is_tile_in_west_wall(tile):
                return self.tile_west_wall_neighbours(tile)

        def is_tile_in_north_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if row == self._row_dimension else False

        def is_tile_in_south_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if row == 0 else False

        def is_tile_in_east_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if col == self._column_dimension else False

        def is_tile_in_west_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if col == 0 else False

        def is_tile_in_north_east_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if row == self._row_dimension and col == self._column_dimension else False

        def is_tile_in_north_west_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if col == 0 and row == self._row_dimension else False

        def is_tile_in_south_east_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if row == 0 and col == self._column_dimension else False

        def is_tile_in_south_west_wall(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return True if col == 0 and row == 0 else False

        def tile_north_wall_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)

            if self.is_tile_in_north_east_wall(tile):
                return self.tile_north_east_neighbours(tile)
            if self.is_tile_in_north_west_wall(tile):
                return self.tile_north_west_neighbours(tile)
            else:
                return [
                    (row, col - 1),
                    (row - 1, col - 1),
                    (row - 1, col),
                    (row - 1, col + 1),
                    (row, col + 1)
                ]

        def tile_south_wall_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)

            if self.is_tile_in_south_east_wall(tile):
                return self.tile_south_east_neighbours(tile)
            if self.is_tile_in_south_west_wall(tile):
                return self.tile_south_west_neighbours(tile)
            else:
                return [
                    (row, col - 1),
                    (row + 1, col - 1),
                    (row + 1, col),
                    (row + 1, col + 1),
                    (row, col + 1)
                ]

        def tile_east_wall_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)

            if self.is_tile_in_north_east_wall(tile):
                return self.tile_north_east_neighbours(tile)
            if self.is_tile_in_south_east_wall(tile):
                return self.tile_south_east_neighbours(tile)
            else:
                return [
                    (row + 1, col),
                    (row + 1, col - 1),
                    (row, col - 1),
                    (row - 1, col - 1),
                    (row - 1, col)
                ]

        def tile_west_wall_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)

            if self.is_tile_in_north_west_wall(tile):
                return self.tile_north_west_neighbours(tile)
            if self.is_tile_in_south_west_wall(tile):
                return self.tile_south_west_neighbours(tile)
            else:
                return [
                    (row + 1, col),
                    (row + 1, col + 1),
                    (row, col + 1),
                    (row - 1, col + 1),
                    (row - 1, col)
                ]

        def tile_north_east_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return [(row, col - 1), (row - 1, col - 1), (row - 1, col)]

        def tile_north_west_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return [(row, col + 1), (row - 1, col + 1), (row - 1, col)]

        def tile_south_east_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return [(row, col - 1), (row + 1, col - 1), (row + 1, col)]

        def tile_south_west_neighbours(self, tile):
            row, col = self.is_tile_in_bound(tile)
            return [(row, col + 1), (row + 1, col + 1), (row + 1, col)]

        ########################################################################
        #				BOARD CLASS UTILITY FUNCTIONS BEGINS				   #
        ########################################################################
        def is_tile_in_bound(self, tile):
            row, col = tile
            return tile

        def print_board(self):
            for row in self._board:
                print(row)

        # since i might find a bomb in which covered tiles around it can be -1
        def is_valid_mine_count(self, tile, mine_count):
            tile_neighbours = self.tile_neighbours(tile)
            tile_neighbours_count = len(tile_neighbours)
            return tile, mine_count

        def is_valid_to_flag(self, tile):
            return tile

        def is_valid_to_unflagg(self, tile):
            return tile

    ########################################################################
    #				BOARD CLASS UTILITY FUNCTIONS ENDS					   #
    ########################################################################

########################################################################
#							BOARD CLASS BEGINS ENDS					   #
########################################################################
