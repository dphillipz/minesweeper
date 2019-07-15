#!/usr/bin/env python

import itertools
import os
import pygame
import random
import sys
import time
import thorpy

from pygame.locals import *

import common

LEFT_MOUSE = 1
RIGHT_MOUSE = 3

class MineCell(common.Cell):
    def __init__(self, r, c, w, h, border, font):
        super().__init__(r, c, w, h, border, font)
    def reset(self):
        super().reset()
        self.hidden = True
        self.mine = False
        self.flagged = False
        self.mine_count = 0
    def count_mines(self):
        self.mine_count = len([n for n in self.neighbors if n.mine])
        mtw, mth = self.font.size(str(self.mine_count))
        mtx = self.bg_rect.width/2 - mtw/2
        mty = self.bg_rect.height/2 - mth/2
        self.mine_text_rect = pygame.Rect(self.bg_rect.x + mtx, self.bg_rect.y + mty, mtw, mth)
    def click(self, button):
        if button == LEFT_MOUSE and not self.flagged:
            self.reveal()
        elif button == RIGHT_MOUSE and self.hidden:
            self.flagged = not self.flagged
            self.dirty = True
    def reveal(self, endgame=False):
        if self.hidden:
            if endgame:
                self.flagged = False # TODO show whether the guess was correct
            self.hidden = False
            self.dirty = True
            if self.mine_count == 0:
                for n in self.neighbors:
                    n.reveal()
    def paint(self, surface):
        if self.dirty:
            self.dirty = False
            bg_colour = (120, 120, 120) if self.selected else (0, 0, 0)
            button_colour = (100, 80, 80) # dug up soil
            if self.flagged:
                button_colour = (40, 40, 160) # bright blue
            elif self.hidden:
                button_colour = (40, 160, 40) # grass
            elif self.mine:
                button_colour = (200, 20, 20) # red for now, someday use a crater tile
            surface.fill(bg_colour, self.bg_rect)
            surface.fill(button_colour, self.button_rect)
            if not self.hidden and not self.mine and self.mine_count > 0:
                mine_text = self.font.render(str(self.mine_count), True, (240, 240, 240), button_colour)
                surface.blit(mine_text, self.mine_text_rect)

class Minefield(common.Gameboard):
    def __init__(self, parent, screen, background, font, rows, columns, mine_count):
        super().__init__(parent, screen, background, font, rows, columns)
        self.mine_count = mine_count
        self.wins = 0
        self.losses = 0
        self.reset()
    def reset(self):
        super().reset_selection()
        self.exploded = False
        self.victory = False
        self.mines = []
    def create_cell(self, row, column, width, height, border, font):
        return MineCell(row, column, width, height, border, font)
    def paint(self):
        if self.exploded:
            pygame.display.set_caption("Game Over!")
            super().paint() # TODO show a game over overlay instead
        elif self.victory:
            pygame.display.set_caption("Victory!")
            super().paint() # TODO show a victory overlay instead
        else:
            super().paint()
    def win(self):
        self.victory = True
        self.wins += 1
        self.reveal_board()
    def lose(self):
        self.exploded = True
        self.losses += 1
        self.reveal_board()
    def click_selected_cell(self, button):
        if button == RIGHT_MOUSE and len(self.mines) == 0:
            return
        c = self.get_cell(self.kb_row, self.kb_col)
        if c is not None: 
            if len(self.mines) == 0:
                self.deploy_mines(c.row, c.column)
            c.click(button)
            if not c.hidden:
                if c.mine:
                    self.lose()
                elif self.mine_count == sum(c.hidden for c in self.cells):
                    self.win()
    def reveal_board(self):
        for c in self.cells:
            c.reveal(True)
    def deploy_mines(self, click_row, click_column):
        m = self.mine_count
        while m > 0:
            next_mine = random.randint(0, self.rows-1), random.randint(0, self.columns-1)
            if next_mine != (click_row, click_column) and next_mine not in self.mines:
                self.mines.append(next_mine)
                self.get_cell(next_mine[0], next_mine[1]).mine = True
                m -= 1
        for c in self.cells:
            c.count_mines()
        for (dr, dc) in itertools.product((-1, 0, 1), (-1, 0, 1)):
            c = self.get_cell(click_row+dr, click_column+dc)
            if c is not None and not c.mine:
                c.reveal()
    def handle_key(self, key):
        if key == K_q:
            self.active = False
        elif not self.exploded and not self.victory:
            if key in (K_UP, K_w):
                self.decrement_kb_row()
            elif key in (K_DOWN, K_s):
                self.increment_kb_row()
            elif key in (K_LEFT, K_a):
                self.decrement_kb_col()
            elif key in (K_RIGHT, K_d):
                self.increment_kb_col()
            elif key in (K_RETURN, K_SPACE):
                self.click_selected_cell(LEFT_MOUSE)
            elif key in (K_BACKSPACE, K_r):
                self.click_selected_cell(RIGHT_MOUSE)
    def handle_mouse_button(self, button, pos):
        if not self.exploded and not self.victory:
            for c in self.cells:
                if c.button_rect.collidepoint(pos):
                    self.unselect_cell(self.kb_row, self.kb_col)
                    self.kb_row, self.kb_col = c.row, c.column
                    c.select()
                    self.click_selected_cell(button)
                elif c.selected:
                    c.unselect()
    def handle_event(self, event):
        if event.type == MOUSEBUTTONUP and not self.exploded:
            self.handle_mouse_button(event.button, event.pos)
        elif event.type == KEYUP:
            self.handle_key(event.key)
        elif event.type == QUIT:
            self.parent.active = False
            self.active = False

class OptionMenu(common.Scene):
    def __init__(self, parent, screen, background, font, rows, columns):
        super().__init__(parent, screen, background, font)
        self.quit_button = thorpy.make_button('Return', func=OptionMenu.quit, params={'self': self})
        self.varset = thorpy.VarSet()
        self.varset.add('rows', value=rows, text='Rows:', limits=(5,20))
        self.varset.add('columns', value=columns, text='Columns:', limits=(5,20))
        self.box = thorpy.ParamSetter([self.varset], elements=[self.quit_button], size=(screen.get_width(), screen.get_height()))
        thorpy.store(self.box)
        self.menu = thorpy.Menu(self.box)
        for element in self.menu.get_population():
            element.surface = self.screen
    def handle_event(self, event):
        if event.type == KEYUP:
            if event.key == K_q:
                self.quit()
        elif event.type != KEYDOWN:
            self.menu.react(event)
    def paint(self):
        self.box.blit()
        self.box.update()
    def quit(self):
        self.rows = self.varset.get_value('rows')
        self.columns = self.varset.get_value('columns')
        self.active = False

class MainMenu(common.Scene):
    def __init__(self, parent, screen, background, font):
        super().__init__(parent, screen, background, font)
        self.rows = 15
        self.columns = 15
        self.mine_count = (self.rows*self.columns)/10
        self.gameboard = Minefield(self, screen, background, font, self.rows, self.columns, self.mine_count)
        self.title = thorpy.make_text('Minesweeper', font_size=20, font_color=(0, 0, 150))
        self.start_button = thorpy.make_button('New Game', func=MainMenu.activate_gameboard, params={'self': self})
        self.options_button = thorpy.make_button('Options', func=MainMenu.activate_options, params={'self': self})
        self.quit_button = thorpy.make_button('Quit', func=MainMenu.quit, params={'self': self})
        self.box = thorpy.Box(elements=[self.title, self.start_button, self.options_button, self.quit_button], size=(screen.get_width(), screen.get_height()))
        thorpy.store(self.box)
        self.menu = thorpy.Menu(self.box)
        for element in self.menu.get_population():
            element.surface = self.screen
    def handle_event(self, event):
        if event.type == KEYUP:
            if event.key == K_q:
                self.quit()
            elif event.key == K_n:
                self.activate_gameboard()
            elif event.key == K_o:
                self.activate_options()
        elif event.type != KEYDOWN:
            self.menu.react(event)
    def paint(self):
        pygame.display.set_caption("Minesweeper!")
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()
        self.box.blit()
        self.box.update()
    def quit(self):
        self.active = False
        print(f'wins {self.gameboard.wins} losses {self.gameboard.losses}')
    def activate_gameboard(self):
        self.gameboard.activate()
        self.gameboard.reset()
        self.gameboard.reset_cells()
    def activate_options(self):
        self.options = OptionMenu(self, self.screen, self.background, self.font, self.rows, self.columns)
        self.options.activate() 
        # TODO need to figure out why rows/columns not being passed up
        self.rows = self.options.rows
        self.columns = self.options.columns
        self.mine_count = (self.rows*self.columns)/10
        self.gameboard = Minefield(self, self.screen, self.background, self.font, self.rows, self.columns, self.mine_count)

def window_init(width, height, caption):
    pygame.display.set_mode((width, height))
    pygame.display.set_caption(caption)
    screen = pygame.display.get_surface()
    background = pygame.Surface(screen.get_size()).convert()
    background.fill((0, 0, 0))
    screen.blit(background, (0, 0))
    pygame.display.flip()
    return screen, background

def main():
    pygame.init()
    thorpy.set_theme('human')
    width = 600
    height = 600
    font = pygame.font.SysFont("Arial", 18)
    screen, background = window_init(width, height, "Minesweeper!")
    main_menu = MainMenu(None, screen, background, font)
    print(screen)
    print(background)
    print(main_menu)
    print(main_menu.screen)
    main_menu.activate()

if __name__ == '__main__':
    main()

