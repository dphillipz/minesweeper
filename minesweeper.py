#!/usr/bin/env python

import itertools
import os
import pygame
import random
import sys
import time

from pygame.locals import *

from scene import *
from gameboard import *

LEFT_MOUSE = 1
RIGHT_MOUSE = 3

class MineCell(Cell):
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

class Minefield(Gameboard):
    def __init__(self, parent, screen, background, font, rows, columns, mine_count):
        super().__init__(parent, screen, background, font, rows, columns)
        self.mine_count = mine_count
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
                    self.exploded = True
                    self.reveal_board()
                elif self.mine_count == sum(c.hidden for c in self.cells):
                    self.victory = True
                    self.reveal_board()
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
    def handle_events(self):
        event = pygame.event.wait()
        if event.type == MOUSEBUTTONUP and not self.exploded:
            self.handle_mouse_button(event.button, event.pos)
        elif event.type == KEYUP:
            self.handle_key(event.key)
        elif event.type == QUIT:
            self.parent.active = False
            self.active = False

class MainMenu(Scene):
    def __init__(self, parent, screen, background, font, rows, columns, mine_count):
        super().__init__(parent, screen, background, font)
        self.gameboard = Minefield(self, screen, background, font, rows, columns, mine_count)
        hcenter = self.screen.get_width()/2
        vcenter = self.screen.get_height()/2
        # render the text here to cache the surfaces and make the rects available to handle_events()
        self.new_game_text, self.new_game_rect = self.render_new_game_text(hcenter, vcenter)
        self.exit_text, self.exit_rect = self.render_exit_text(hcenter, vcenter)
    def render_new_game_text(self, hcenter, vcenter):
        new_game_text = self.font.render('New Game', True, (240, 240, 240), (0, 0, 0))
        new_game_rect = new_game_text.get_rect()
        new_game_rect.left = hcenter - new_game_rect.width/2
        new_game_rect.top = vcenter - 3*new_game_rect.height/2
        return new_game_text, new_game_rect
    def render_exit_text(self, hcenter, vcenter):
        exit_text = self.font.render('Exit Game', True, (192, 192, 192), (0, 0, 0))
        exit_rect = exit_text.get_rect()
        exit_rect.left = hcenter - exit_rect.width/2
        exit_rect.top = vcenter + exit_rect.height/2
        return exit_text, exit_rect
    def paint(self):
        pygame.display.set_caption("Minesweeper!")
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.new_game_text, self.new_game_rect)
        self.screen.blit(self.exit_text, self.exit_rect)
        pygame.display.flip()
    def handle_events(self):
        event = pygame.event.wait()
        if event.type == MOUSEBUTTONUP:
            if self.exit_rect.collidepoint(event.pos):
                self.active = False
            elif self.new_game_rect.collidepoint(event.pos):
                self.activate_gameboard()
        elif event.type == KEYUP:
            if event.key == K_q:
                self.active = False
            elif event.key == K_n:
                self.activate_gameboard()
            elif event.key == K_d and pygame.key.get_mods() & KMOD_CTRL:
                self.gameboard.toggle_debug()
        elif event.type == QUIT:
            self.active = False
    def activate_gameboard(self):
        self.gameboard.activate()
        self.gameboard.reset()
        self.gameboard.reset_cells()

def load_image(name, colorkey=None):
    try:
        image = pygame.image.load(name).convert()
    except pygame.error as message:
        print(f"Cannot load image: {name}")
        raise
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

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
    width = 600
    height = 600
    rows = 15
    columns = 15
    mine_count = 20
    pygame.init()
    font = pygame.font.SysFont("Arial", 18)
    screen, background = window_init(width, height, "Minesweeper!")
    main_menu = MainMenu(None, screen, background, font, rows, columns, mine_count)
    main_menu.activate()

if __name__ == '__main__':
    main()

