#!/usr/bin/python3
from random import getrandbits, random
from argparse import ArgumentParser
from time import time
import pygame


WIDTH = 800
HEIGHT = 600
CELL_SIZE = 10
ROWS = None
COLUMNS = None

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)

# Global variables
window = None
running = False
generation = 0
clock = None
cells = []
limit_fps = True
gps = 0.0
gps_counter = 0
change_list = set()
next_change_list = set()
draw_list = set()


class Cell:
    def __init__(self, row, column) -> None:
        self.row = row
        self.column = column
        self.state = False
        self.next_state = False
        self.neighbours = []
        self.alive_neighbours = 0
        self.changed_state = True

    def make_alive(self):
        if not self.state:
            change_list.add(self)
            draw_list.add(self)
            for neighbour in self.neighbours:
                neighbour.alive_neighbours += 1
                change_list.add(neighbour)
            self.state = True
            self.next_state = True
            self.changed_state = True

    def make_dead(self):
        if self.state:
            draw_list.add(self)
            for neighbour in self.neighbours:
                neighbour.alive_neighbours -= 1
            self.state = False
            self.next_state = False

    def update_neighbours(self):
        for row in range(self.row-1, self.row+2):
            for column in range(self.column-1, self.column+2):
                if not (row == self.row and column == self.column):
                    if 0 <= row < ROWS and 0 <= column < COLUMNS:
                        self.neighbours.append(cells[row][column])

        draw_list.add(self)
        if self.state:
            change_list.add(self)
            for neighbor in self.neighbours:
                neighbor.alive_neighbours += 1
                change_list.add(neighbor)

    def calculate_next_state(self):
        if self.state:
            if self.alive_neighbours < 2 or self.alive_neighbours > 3:
                self.next_state = False
        else:
            if self.alive_neighbours == 3:
                self.next_state = True

    def update_state(self):
        if self.state != self.next_state:
            draw_list.add(self)
            next_change_list.add(self)
            if self.next_state:
                for neighbour in self.neighbours:
                    neighbour.alive_neighbours += 1
                    next_change_list.add(neighbour)
            else:
                for neighbour in self.neighbours:
                    neighbour.alive_neighbours -= 1
                    next_change_list.add(neighbour)
            self.state = self.next_state

    def draw(self):
        pygame.draw.rect(window, WHITE if self.state else GREY,  [
            self.column*CELL_SIZE, self.row*CELL_SIZE, CELL_SIZE, CELL_SIZE])


def parse_args():
    global WIDTH, HEIGHT, CELL_SIZE, ROWS, COLUMNS, running, limit_fps

    parser = ArgumentParser(
        description="A program to simulate John Conway's Game of Life.", usage="* Click on cell to make it alive.\n* Right click on cell to make it dead.\n* Press DELETE to clear grid.")
    parser.add_argument("--width",
                        "-w", type=int, help="Set width of window, defaults to 800.", default=WIDTH)
    parser.add_argument("--height",
                        "-ht", type=int, help="Set height of window, defaults to 600.", default=HEIGHT)
    parser.add_argument("--cellsize",
                        "-c", type=int, help="Set the size of a cell, defaults to 10.", default=CELL_SIZE)
    parser.add_argument(
        "--run", "-r", help="Starts the program immediately without waiting for user to press space.", action='store_true')
    parser.add_argument(
        "--no_limit", "-n", help="Sets the fps limit of program to infinty. Default is 60.", action='store_false')
    args = parser.parse_args()
    WIDTH = args.width
    HEIGHT = args.height
    CELL_SIZE = args.cellsize
    ROWS = HEIGHT//CELL_SIZE
    COLUMNS = WIDTH//CELL_SIZE
    running = args.run
    limit_fps = args.no_limit


def init_pygame():
    print("Initialising screen...")
    global window, clock
    window = pygame.display.set_mode(
        (WIDTH, HEIGHT), pygame.HWACCEL, pygame.HWSURFACE)
    window.set_alpha(None)
    pygame.display.set_caption("Game of Life")
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])
    clock = pygame.time.Clock()


def init_cells():
    global cells
    print("Making cells...")
    cells = [[(Cell(row, column)) for column in range(WIDTH)]
             for row in range(HEIGHT)]
    print("Preparing cells...")
    for row in cells:
        for cell in row:
            cell.update_neighbours()
    random_grid()


def random_grid():
    global generation
    generation = 0
    for row in cells:
        for cell in row:
            cell.make_dead()
            draw_list.add(cell)
    change_list.clear()
    for row in cells:
        for cell in row:
            if random() < 0.15:
                cell.make_alive()
                draw_list.add(cell)


def handle_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                global running, gps, gps_counter
                running = not running
                gps_counter = 0
                gps = 0.0
            if not running:
                if event.key == pygame.K_BACKSPACE:
                    global generation
                    for row in cells:
                        for cell in row:
                            cell.make_dead()
                            draw_list.add(cell)
                    generation = 0
                    change_list.clear()
                if event.key == pygame.K_r:
                    random_grid()

    if not running:
        if pygame.mouse.get_pressed()[0]:
            x, y = pygame.mouse.get_pos()
            row = y // CELL_SIZE
            column = x // CELL_SIZE
            cells[row][column].make_alive()
        if pygame.mouse.get_pressed()[2]:
            x, y = pygame.mouse.get_pos()
            row = y // CELL_SIZE
            column = x // CELL_SIZE
            cells[row][column].make_dead()


def print_status():
    print(chr(27) + "[2J")
    print(chr(27) + "[1;1f")
    print("Generation: "+str(generation))
    print("State: Running" if running else "State: Paused")
    print("GenPerSec: "+str(gps))
    print("Active cells: "+str(len(change_list)))
    print("Cells to draw: "+str(len(draw_list)))


def draw_cells():
    for cell in draw_list:
        cell.draw()
    draw_list.clear()
    pygame.display.update()


def update():
    global change_list, generation, gps_counter
    draw_cells()
    if running:
        for cell in change_list:
            cell.calculate_next_state()
        for cell in change_list:
            cell.update_state()
        change_list = next_change_list.copy()
        next_change_list.clear()
        generation += 1
        gps_counter += 1
    print_status()
    if limit_fps or not running:
        clock.tick(60)


def main():
    global gps, gps_counter
    parse_args()
    init_cells()
    init_pygame()
    start_time = time()
    while True:
        handle_events()
        update()
        if (time() - start_time) > 1:
            gps = str(gps_counter / (time() - start_time))
            gps = gps[:gps.find(".")+3]+" G/s"
            gps_counter = 0
            start_time = time()


if __name__ == "__main__":
    main()
