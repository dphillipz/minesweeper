#!/usr/bin/env python

import pygame
import os
import random
import sys
import time

from pygame.locals import *

from scene import *

LEFT_MOUSE = 1
RIGHT_MOUSE = 3

class Cell(object):
    def __init__(self, r, c, w, h, border):
        self.row = r
        self.column = c
        self.bg_rect = pygame.Rect(c*h, r*w, w, h)
        self.button_rect = pygame.Rect(c*h + border, r*w + border, w - 2*border, h - 2*border)
        self.reset()
    def reset(self):
        self.hidden = True
        self.mine = False
        self.flagged = False
        self.dirty = True
        self.selected = False
    def select(self):
        self.selected = True
        self.dirty = True
    def unselect(self):
        self.selected = False
        self.dirty = True
    def click(self, button):
        if button == LEFT_MOUSE and not self.flagged:
            self.hidden = False
            self.dirty = True
        elif button == RIGHT_MOUSE:
            self.flagged = not self.flagged
            self.dirty = True
    def paint(self, surface):
        if self.dirty:
            self.dirty = False
            if self.selected:
                surface.fill((120, 120, 120), self.bg_rect)
            else:
                surface.fill((0, 0, 0), self.bg_rect)
            if self.flagged:
                surface.fill((40, 40, 160), self.button_rect) # bright blue
            elif self.hidden:
                surface.fill((40, 160, 40), self.button_rect) # grass
            elif self.mine:
                surface.fill((200, 20, 20), self.button_rect) # red for now, someday use a crater tile
            else:
                surface.fill((100, 80, 80), self.button_rect) # dug up soil

class Gameboard(Scene):
    def __init__(self, parent, screen, background, font, rows, columns, mine_count):
        super().__init__(parent, screen, background, font)
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count
        self.disable_mines = False
        self.debug_enabled = False
        self.cells = []
        self.reset()
        self.make_grid()
    def reset(self):
        self.exploded = False
        self.mines = []
        self.kb_row = 0
        self.kb_col = 0
    def reset_cells(self):
        for c in self.cells:
            c.reset()
    def make_grid(self):
        cw = self.screen.get_width() / self.columns
        ch = self.screen.get_height() / self.rows
        for r in range(self.rows):
            for c in range(self.columns):
                self.cells.append(Cell(r, c, cw, ch, 2))
    def paint(self):
        for c in self.cells:
            c.paint(self.screen)
        pygame.display.flip()
        if self.exploded:
            pass # TODO show a game over overlay
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
    def click_selected_cell(self, button):
        if button == RIGHT_MOUSE and len(self.mines) == 0:
            return
        c = self.get_cell(self.kb_row, self.kb_col)
        if c is not None: 
            if len(self.mines) == 0:
                self.deploy_mines(c.row, c.column)
            c.click(button)
            if not c.hidden and c.mine and not self.disable_mines:
                self.exploded = True
                self.reveal_board()
    def toggle_debug(self):
        self.debug_enabled = not self.debug_enabled
        if not self.debug_enabled:
            self.disable_mines = False
    def reveal_mines(self):
        if self.debug_enabled:
            for m in self.mines:
                self.kb_row, self.kb_col = m
                self.click_selected_cell(LEFT_MOUSE)
    def reveal_board(self):
        for c in self.cells:
            if c.hidden:
                c.click(LEFT_MOUSE)
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
    def deploy_mines(self, click_row, click_column):
        m = self.mine_count
        while m > 0:
            next_mine = random.randint(0, self.rows-1), random.randint(0, self.columns-1)
            if next_mine != (click_row, click_column) and next_mine not in self.mines:
                self.mines.append(next_mine)
                self.get_cell(next_mine[0], next_mine[1]).mine = True
                m -= 1
    def handle_events(self):
        event = pygame.event.wait()
        if event.type == MOUSEBUTTONUP and not self.exploded:
            for c in self.cells:
                if c.button_rect.collidepoint(event.pos):
                    self.unselect_cell(self.kb_row, self.kb_col)
                    self.kb_row, self.kb_col = c.row, c.column
                    c.select()
                    self.click_selected_cell(event.button)
                elif c.selected:
                    c.unselect()
        elif event.type == KEYUP:
            if event.key == K_q:
                self.active = False
            elif self.debug_enabled and event.key == K_m and pygame.key.get_mods() & KMOD_CTRL:
                self.disable_mines = not self.disable_mines
            elif self.debug_enabled and event.key == K_r and pygame.key.get_mods() & KMOD_CTRL:
                if len(self.mines) > 0:
                    self.reveal_mines()
            elif not self.exploded:
                if event.key == K_UP:
                    self.decrement_kb_row()
                elif event.key == K_DOWN:
                    self.increment_kb_row()
                elif event.key == K_LEFT:
                    self.decrement_kb_col()
                elif event.key == K_RIGHT:
                    self.increment_kb_col()
                elif event.key == K_RETURN:
                    self.click_selected_cell(LEFT_MOUSE)
                elif event.key == K_BACKSPACE:
                    self.click_selected_cell(RIGHT_MOUSE)
        elif event.type == QUIT:
            self.parent.active = False
            self.active = False

class MainMenu(Scene):
    def __init__(self, parent, screen, background, font, rows, columns, mine_count):
        super().__init__(parent, screen, background, font)
        self.gameboard = Gameboard(self, screen, background, font, rows, columns, mine_count)
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
                self.gameboard.activate()
                self.gameboard.reset()
                self.gameboard.reset_cells()
        elif event.type == KEYUP:
            if event.key == K_q:
                self.active = False
            elif event.key == K_n:
                self.gameboard.activate()
                self.gameboard.reset()
                self.gameboard.reset_cells()
            elif event.key == K_d and pygame.key.get_mods() & KMOD_CTRL:
                self.gameboard.toggle_debug()
        elif event.type == QUIT:
            self.active = False

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

def event_init():
    pygame.event.set_allowed(None)
    pygame.event.set_allowed(MOUSEBUTTONUP)
    pygame.event.set_allowed(MOUSEBUTTONDOWN)
    pygame.event.set_allowed(KEYUP)
    pygame.event.set_allowed(KEYDOWN)
    pygame.event.set_allowed(QUIT)

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
    rows = 10
    columns = 10
    mine_count = 20
    pygame.init()
    event_init()
    font = pygame.font.SysFont("Arial", 18)
    screen, background = window_init(width, height, "Minesweeper!")
    main_menu = MainMenu(None, screen, background, font, rows, columns, mine_count)
    main_menu.activate()

if __name__ == '__main__':
    main()

