#!/usr/bin/env python

import itertools
import pygame

class Scene(object):
    def __init__(self, parent, screen, background, font):
        self.parent = parent
        self.screen = screen
        self.background = background
        self.font = font
        self.active = False
    def activate(self):
        self.active = True
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()
        self.run()
    def run(self):
        while(self.active):
            self.paint()
            self.handle_events()
    def paint(self):
        print('Unimplemented paint() function!')
    def handle_events(self):
        print('Unimplemented handle_events() function!')

class Cell(object):
    def __init__(self, r, c, w, h, border, font):
        self.row = r
        self.column = c
        self.font = font
        self.bg_rect = pygame.Rect(c*h, r*w, w, h)
        self.button_rect = pygame.Rect(c*h + border, r*w + border, w - 2*border, h - 2*border)
        self.neighbors = []
        self.reset()
    def __eq__(self, other):
        return self.row == other.row and self.column == other.column
    def add_neighbor(self, neighbor):
        if neighbor is not None and neighbor != self and neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
    def select(self):
        self.selected = True
        self.dirty = True
    def unselect(self):
        self.selected = False
        self.dirty = True
    def paint(self, surface):
        if self.dirty:
            self._paint(surface)
            self.dirty = False
    def reset(self):
        self.dirty = True
        self.selected = False
    def click(self, button):
        pass
    def _paint(self, surface):
        pass

class Gameboard(Scene):
    def __init__(self, parent, screen, background, font, rows, columns):
        super().__init__(parent, screen, background, font)
        self.rows = rows
        self.columns = columns
        self.cells = []
        self.reset_selection()
        self.make_grid()
    def reset_selection(self):
        self.kb_row = 0
        self.kb_col = 0
    def make_grid(self):
        cw = self.screen.get_width() / self.columns
        ch = self.screen.get_height() / self.rows
        for (r,c) in itertools.product(range(self.rows), range(self.columns)):
            self.cells.append(self.create_cell(r, c, cw, ch, 2, self.font))
        for (r,c) in itertools.product(range(self.rows), range(self.columns)):
            for (dr, dc) in itertools.product((-1, 0, 1), (-1, 0, 1)):
                self.get_cell(r, c).add_neighbor(self.get_cell(r+dr, c+dc))
    def create_cell(self, row, column, width, height, border, font):
        return Cell(row, column, width, height, border, font)
    def reset_cells(self):
        for c in self.cells:
            c.reset()
    def paint(self):
        for c in self.cells:
            c.paint(self.screen)
        pygame.display.flip()
    def get_cell(self, row, column):
        if 0 <= row < self.rows and 0 <= column < self.columns:
            return self.cells[row*self.columns + column]
    def select_cell(self, row, column):
        c = self.get_cell(row, column)
        if c is not None: 
            c.select()
    def unselect_cell(self, row, column):
        c = self.get_cell(row, column)
        if c is not None: 
            c.unselect()
    def increment_kb_row(self):
        self.unselect_cell(self.kb_row, self.kb_col)
        if self.kb_row == (self.rows - 1):
            self.kb_row = 0
        else:
            self.kb_row = self.kb_row + 1
        self.select_cell(self.kb_row, self.kb_col)
    def decrement_kb_row(self):
        c = self.unselect_cell(self.kb_row, self.kb_col)
        if self.kb_row == 0:
            self.kb_row = self.rows - 1
        else:
            self.kb_row = self.kb_row - 1
        self.select_cell(self.kb_row, self.kb_col)
    def increment_kb_col(self):
        self.unselect_cell(self.kb_row, self.kb_col)
        if self.kb_col == (self.columns - 1):
            self.kb_col = 0
        else:
            self.kb_col = self.kb_col + 1
        self.select_cell(self.kb_row, self.kb_col)
    def decrement_kb_col(self):
        self.unselect_cell(self.kb_row, self.kb_col)
        if self.kb_col == 0:
            self.kb_col = self.columns - 1
        else:
            self.kb_col = self.kb_col - 1
        self.select_cell(self.kb_row, self.kb_col)

if __name__ == '__main__':
    print('common.py is a library:')
    print('from common import *')

