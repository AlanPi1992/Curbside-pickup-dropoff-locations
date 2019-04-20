import os
import numpy as np

class Cell():
    """The hexagon cells in the grid for the study area"""
    def __init__(self, row, column):
        self.row = row
        self.col = column
        self.demand = 0
        self.supply = 0
        self.service_rate_kernel = [] # service rates for the cell; the 6 cells around; the 12 cells around the 6 cells; and so on.
        self.supply_kernel = {}
        self.is_candidate = False
        self.fixed_cost = 0
        self.operational_cost = 0
        
    def set_demand(self, demand):
        self.demand = demand
        
    def set_to_candidate(self):
        self.is_candidate = True
    
    def set_costs(self, fcost, ocost):
        self.fixed_cost = fcost
        self.operational_cost = ocost
        
    def set_service_rate_kernel(self, srkernel):
        self.service_rate_kernel = srkernel

    def clear_supply(self):
        self.supply = 0


class Grid(object):
    """The grid for the study area"""
    def __init__(self, n_rows, n_cols, candidate_list, costs_list, srkernel_list, demand_matrix):
        self.n_rows = n_rows
        self.n_cols = n_cols
        self.cells = [[Cell(i, j) for j in range(n_cols)] for i in range(n_rows)]
        self.candidate_list = candidate_list
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                self.cells[i][j].set_demand(demand_matrix[i][j])
        for k in range(len(candidate_list)):
            self.cells[candidate_list[k][0]][candidate_list[k][1]].set_to_candidate()
            self.cells[candidate_list[k][0]][candidate_list[k][1]].set_costs(costs_list[k][0], costs_list[k][1])
            self.cells[candidate_list[k][0]][candidate_list[k][1]].set_service_rate_kernel(srkernel_list[k])
        self.generate_supply_kernel_for_candidates()

    def generate_supply_kernel_for_candidates(self):
        for (row, col) in self.candidate_list:
            # generate valid indices set around current candidate
            _valid_indices_set = []
            _sr_kernel = self.cells[row][col].service_rate_kernel
            _row_offsets = [e for e in range(-len(_sr_kernel), len(_sr_kernel)-1)]
            if col % 2 == 0:
                _flag = 0
            else:
                _flag = 1
            for j in range(len(_sr_kernel)-1):
                for i in _row_offsets:
                    if (row + i >= 0) and (row + i < self.n_rows):
                        if (col + j >= 0) and (col + j < self.n_cols):
                            if (row + i, col + j) not in _valid_indices_set:
                                _valid_indices_set.append((row + i, col + j))
                        if (col - j >= 0) and (col - j < self.n_cols):
                            if (row + i, col - j) not in _valid_indices_set:
                                _valid_indices_set.append((row + i, col - j))
                if _flag == 0:
                    _row_offsets = _row_offsets[1:]
                else:
                    _row_offsets = _row_offsets[:-1]
                _flag = 1 - _flag
                
            # for all valid indices, generate supply kernel
            _tot = 0
            for (i, j) in _valid_indices_set:
                _dist = abs(i-row) + abs(j-col) #simplified version
                if _dist > len(_sr_kernel)-1:
                    _dist = len(_sr_kernel)-1
                self.cells[row][col].supply_kernel[(i, j)] = _sr_kernel[_dist] * self.cells[i][j].demand
                _tot += self.cells[row][col].supply_kernel[(i, j)]
            for (i, j) in _valid_indices_set:
                self.cells[row][col].supply_kernel[(i, j)] /= _tot
            
                
    # set all cells' supply to 0
    def clear_supply(self):
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                self.cells[i][j].clear_supply()

    # the unmet pickup/dropoff demand
    def unmet_demand(self):
        _unmet = 0
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                _unmet += max(0, self.cells[i][j].demand - self.cells[i][j].supply)
        return _unmet

    # update the whole grid supply caused by selecting one candidate location
    def update_supply(self, row_index, column_index, total_supply):
        for (i,j) in self.cells[row_index][column_index].supply_kernel.keys():
            # print(row_index, column_index,i,j)
            _s = round(self.cells[row_index][column_index].supply_kernel[(i,j)] * total_supply)
            assert i < self.n_rows, "row index too large"
            assert i >= 0, "row index less than 0"
            assert j < self.n_cols, "column index too large"
            assert j >= 0, "column index less than 0"
            self.cells[i][j].supply += _s

    # check the contribution of selecting one candidate loction without updating the grid supply
    def contribution_of_one_cadidate(self, row_index, column_index, total_supply):
        _tot = 0
        for (i,j) in self.cells[row_index][column_index].supply_kernel.keys():
            _s = round(self.cells[row_index][column_index].supply_kernel[(i,j)] * total_supply)
            assert i < self.n_rows, "row index too large"
            assert i >= 0, "row index less than 0"
            assert j < self.n_cols, "column index too large"
            assert j >= 0, "column index less than 0"
            if _s + self.cells[i][j].supply < self.cells[i][j].demand:
                _tot += _s
            else:
                _tot += max(0, self.cells[i][j].demand - self.cells[i][j].supply)
        return _tot
