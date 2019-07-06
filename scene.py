#!/usr/bin/env python

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

if __name__ == '__main__':
    print('scene.py is a library:')
    print('from scene import *')

