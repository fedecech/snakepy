from enum import Enum
import random
import curses
import time
from curses import wrapper
import os
import sys
import select

HEIGTH = 20
WIDTH = 20
MAX_SPEED = 0.1
LEADERBOARD_FILE = "leaderboard.txt"

def display_gameover(stdscr):
    stdscr.clear()
    stdscr.nodelay(False)
    stdscr.addstr(0, 0, "Game over\n")
    stdscr.refresh()

def username_input(stdscr):
    curses.echo()
    stdscr.addstr(1, 0, "Enter your username: ")
    stdscr.refresh()
    username = stdscr.getstr(1, 22, 8)
    stdscr.clear()
    return username 

def display_leaderboard():
    pass

def find_pos_in_file(lines, score):
    prev_score = 0 
    for i, line in enumerate(lines):
        (_, c_score) = line.strip().split("-")
        if i > 0 and int(c_score) < score and prev_score > score:
            return i
        prev_score = int(c_score)
    return 0

def end_game(stdscr, score):
    display_gameover(stdscr)

    username = username_input(stdscr)

    stdscr.addstr(0, 0, "LEADERBOARD\n")

    file = open(LEADERBOARD_FILE, "r")
    lines = file.readlines()
    pos = find_pos_in_file(lines, score)

    lines.insert(pos, f"{username.decode('utf-8')}-{score}\n")

    out = open(LEADERBOARD_FILE, "w")
    out.writelines(lines)
    out.close()


    file = open(LEADERBOARD_FILE, "r")
    lines = file.readlines()
    for i, line in enumerate(lines):
        (c_username, c_score) = line.strip().split("-")
        if i == pos:
            stdscr.addstr(i + 3, 0, f"{i+1} \t {c_score} \t {c_username} (you)\n", curses.color_pair(1))
        else:
            stdscr.addstr(i + 3, 0, f"{i+1} \t {c_score} \t {c_username} \n")
        
        if i == len(lines)-1:
            stdscr.addstr(i + 5, 0, "Press q to quit\n")
    
    stdscr.refresh()
    curses.noecho()
    
    c = stdscr.getch()
    while c != ord("q"):
        c = stdscr.getch()

    curses.endwin()
    sys.exit(2)



def generate_food(player):
    new_food = Pos(random.randint(0, HEIGTH), random.randint(0, WIDTH))

    if player.is_in(new_food.r, new_food.c) or player.head == new_food:
        return generate_food(player)
    return new_food

def is_food(foods, r, c):
    for f in foods:
        if f.r == r and f.c == c:
            return True
    return False

def print_board(stdscr, player, foods, score):
    t_str = f"SCORE: {score}\n"
    for r in range(HEIGTH):
        row_str = ""
        for c in range(WIDTH):
            if player.head == Pos(r, c): row_str += "@"
            elif player.is_in(r, c): row_str += "#"
            elif is_food(foods, r, c): row_str += "*"
            else: row_str += "."
        t_str += row_str + "\n" 
    stdscr.addstr(0, 0, t_str) 
    stdscr.refresh()
       
class Pos:
    def __init__(self, r, c):
        self.c = c
        self.r = r

    def __eq__(self, other):
        return self.c == other.c and self.r == other.r
    
class DIR(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

class Player:
    def __init__(self):
        self.head = Pos(WIDTH//2, HEIGTH//2)
        self.body = []


    def is_in(self, r, c):

        for p in self.body:
            if p.c == c and p.r == r: return True

        return False


    def move(self, dirr):
        prev = Pos(self.head.r, self.head.c)

        if dirr == DIR.UP:
            self.head.r = (prev.r - 1)%HEIGTH
        elif dirr == DIR.DOWN:
            self.head.r = (prev.r + 1)%HEIGTH
        elif dirr == DIR.LEFT:
            self.head.c = (prev.c - 1)%WIDTH
        elif dirr == DIR.RIGHT:
            self.head.c = (prev.c + 1)%WIDTH

        for i in range(len(self.body)):
            tmp = Pos(self.body[i].r, self.body[i].c) 
            self.body[i] = prev
            prev = tmp

    def is_eating_itself(self):
        return self.is_in(self.head.r, self.head.c)

    def grow(self, dirr):
        last = self.head if len(self.body) == 0 else self.body[len(self.body) - 1]
        real_dir = dirr

        if len(self.body) >= 2:
            before_last = self.body[len(self.body) - 2]

            if last.c == before_last.c:
                if last.r > before_last.r:
                   real_dir = DIR.DOWN 
                else:
                   real_dir = DIR.UP 
            else:
                if last.c > before_last.c:
                   real_dir = DIR.LEFT 
                else:
                   real_dir = DIR.RIGHT 

        if real_dir == DIR.UP:
            self.body.append(Pos(last.r - 1, last.c))
        elif real_dir == DIR.DOWN:
            self.body.append(Pos(last.r + 1, last.c))
        elif real_dir == DIR.LEFT:
            self.body.append(Pos(last.r, last.c + 1))
        elif real_dir == DIR.RIGHT:
            self.body.append(Pos(last.r, last.c - 1))


            
def main(stdscr):
    player = Player()
    foods = []
    score = 0

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.noecho()
    curses.cbreak()
    stdscr.nodelay(True)
    dirr = DIR.UP

    while True:
        try:
            c = stdscr.getkey()
            if c == "q":
                curses.endwin()
                sys.exit(0)
            elif c == "a":
               dirr = DIR.LEFT 
            elif c == "d":
               dirr = DIR.RIGHT
            elif c == "s":
               dirr = DIR.DOWN
            elif c == "w":
               dirr = DIR.UP
        except Exception as e:
            pass

        player.move(dirr)
        print_board(stdscr, player, foods, score) 

        if player.is_eating_itself():
            end_game(stdscr, score)

        if random.randint(0, 5) == 0:
            foods.append(generate_food(player))

        for f in foods:
            if f == player.head:
                player.grow(dirr)
                score += 10
                foods.remove(f)
                break


        sleep_time = 0.5 if score == 0 else (0.5 - (score / 1000)) 
        time.sleep(sleep_time if sleep_time >= MAX_SPEED else MAX_SPEED)


if __name__ == "__main__":
    wrapper(main)
