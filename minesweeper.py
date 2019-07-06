#!/usr/bin/env python

import pygame
import os
import random
import sys
import time

from pygame.locals import *

from scene import *

WIDTH = 600
HEIGHT = 600

class Cell(object):
    def __init__(self, r, c, w, h, border):
        self.row = r
        self.column = c
        self.rect = pygame.Rect(r*w + border, c*h + border, w - 2*border, h - 2*border)
        self.hidden = True
        self.mine = False
        self.flagged = False
        self.dirty = True
    def reset(self):
        self.hidden = True
        self.mine = False
        self.flagged = False
        self.dirty = True
    def click(self, button):
        if button == 1 and not self.flagged:
            self.hidden = False
            self.dirty = True
        elif button == 3:
            self.flagged = not self.flagged
            self.dirty = True
    def paint(self, surface):
        if self.dirty:
            self.dirty = False
            if self.flagged:
                surface.fill((40, 40, 40), self.rect)
            elif self.hidden:
                surface.fill((60, 60, 120), self.rect)
            elif self.mine:
                surface.fill((240, 0, 0), self.rect)
            else:
                surface.fill((0, 150, 50), self.rect)

class Gameboard(Scene):
    def __init__(self, parent, screen, background, font):
        super().__init__(parent, screen, background, font)
        self.cells = []
        self.mines = []
        self.rows = 10
        self.columns = 10
        self.exploded = False
        self.make_grid()
    def paint(self):
        for c in self.cells:
            c.paint(self.screen)
        pygame.display.flip()
        if self.exploded:
            pass # TODO show a game over overlay
    def handle_events(self):
        event = pygame.event.wait()
        if event.type == MOUSEBUTTONUP:
            if self.exploded:
                return
            if len(self.mines) == 0:
                self.deploy_mines(1)
            for c in self.cells:
                if c.rect.collidepoint(event.pos):
                    c.click(event.button)
                    if not c.hidden and c.mine:
                        self.exploded = True
                    break
        elif event.type == KEYUP:
            if event.key == K_q:
                self.active = False
            # TODO add support for arrow keys, enter, and backspace
        elif event.type == QUIT:
            self.parent.active = False
            self.active = False
    def get_cell(self, r, c):
        return self.cells[r*self.columns + c]
    def deploy_mines(self, mine_count):
        self.mines.append((2,2))
        self.get_cell(2, 2).mine = True
    def reset(self):
        self.exploded = False
        self.mines = []
        for c in self.cells:
            c.reset()
    def make_grid(self):
        cw = self.screen.get_width() / self.columns
        ch = self.screen.get_height() / self.rows
        for r in range(self.rows):
            for c in range(self.columns):
                self.cells.append(Cell(r, c, cw, ch, 2))

class MainMenu(Scene):
    def __init__(self, parent, screen, background, font):
        super().__init__(parent, screen, background, font)
        self.gameboard = Gameboard(self, screen, background, font)
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
        elif event.type == KEYUP:
            if event.key == K_q:
                self.active = False
            elif event.key == K_n:
                self.gameboard.activate()
                self.gameboard.reset()
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
    pygame.init()
    event_init()
    font = pygame.font.SysFont("Arial", 18)
    screen, background = window_init(WIDTH, HEIGHT, "Minesweeper!")
    main_menu = MainMenu(None, screen, background, font)
    main_menu.activate()

if __name__ == '__main__':
    main()

