#!/usr/bin/env python

import kivy
kivy.require('1.2.0') # replace with your current kivy version !

from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color
from kivy.graphics.vertex_instructions import Bezier, Triangle, Rectangle
from kivy.uix.floatlayout import FloatLayout

import random
import math
from pygame import Rect


def diff(a, b):
    return (a[0] - b[0], a[1] - b[1])

def distance(a, b):
    d = diff(a, b)
    return math.sqrt(d[0]**2 + d[1]**2)

def unit_vector_scaled(v, scale):
    modulo = math.sqrt(v[0]**2 + v[1]**2)
    return (v[0] * 5 / modulo, v[1] * 5 / modulo)

class Drawable(object):
    def __init__(self, canvas, group_name):
        self.canvas = canvas
        self.group_name = group_name

    def remove(self):
        self.canvas.remove_group(self.group_name)

    def update(self, dt):
        self.remove()

    def center_pos(self):
        return (self.pos[0] + self.size[0] / 2,
                self.pos[1] + self.size[1] / 2)


class Player(Drawable):
    def __init__(self, size, canvas):
        super(Player, self).__init__(canvas, self.__class__.__name__)
        self.size = (size, size)
        self.pos = (100, Window.size[1]/2 - size/2)
        self.lifes = 3

    def update(self, dt):
        super(Player, self).update(dt)
        (px, py) = self.pos
        (sx, sy) = self.size
        with self.canvas:
            Bezier(points=[px, py, px + sx, py + sy/2], group=self.group_name)
            Bezier(points=[px + sx, py + sy/2, px, py + sy], group=self.group_name)
            Bezier(points=[px, py + sy, px, py], group=self.group_name)

            for i in range(self.lifes):
                Bezier(points=[px, py + i * sy/3, px + sx/3, py + i * sy/3 + sy/6], group=self.group_name)
                Bezier(points=[px + sx/3, py + i * sy/3 + sy/6, px, py + (i+1) * sy/3], group=self.group_name)
                Bezier(points=[px, py + (i+1) * sy/3, px, py + i * sy/3], group=self.group_name)

    def move_up(self):
        if self.pos[1]:
            self.pos = (self.pos[0], self.pos[1] - 1)

    def move_down(self):
        if self.pos[1] + self.size[1] < Window.size[1]:
            self.pos = (self.pos[0], self.pos[1] + 1)

    def move_left(self):
        if self.pos[0]:
            self.pos = (self.pos[0] - 1, self.pos[1])

    def move_right(self):
        if self.pos[0] + self.size[0] < Window.size[0]:
            self.pos = (self.pos[0] + 1, self.pos[1])

    def collision(self, rect):
        for i in range(0, self.size[0], 2):
            if rect.collidepoint(self.pos[0] + i, self.pos[1] + i/2):
                return True
            if rect.collidepoint(self.pos[0] + i, self.pos[1] + self.size[1] - i/2):
                return True
            if rect.collidepoint(self.pos[0], self.pos[1] + i):
                return True
        return False


class Pew(Drawable):
    def __init__(self, canvas, pos, instance):
        self.pos = pos
        super(Pew, self).__init__(canvas, self.__class__.__name__ + str(instance))

    def update(self, dt):
        super(Pew, self).update(dt)
        self.pos = (self.pos[0] + 10, self.pos[1])
        with self.canvas:
            Bezier(points=[self.pos[0], self.pos[1], self.pos[0] + 30, self.pos[1]],
                   group=self.group_name)

    def destroy(self):
        self.pos = (self.pos[0] + Window.size[0], self.pos[1])
        self.remove()

class Enemy(Drawable):
    def __init__(self, canvas, instance):
        self.size = (20, 20)
        self.speed = random.randint(1, 4)
        self.pos = (Window.size[0], random.randint(0, Window.size[1] - self.size[1]))
        super(Enemy, self).__init__(canvas, self.__class__.__name__ + str(instance))

    def update(self, dt, approach_to):
        super(Enemy, self).update(dt)

        distance_to_player = distance(approach_to, self.center_pos())
        if distance_to_player < 200:
            d = diff(approach_to, self.center_pos())
            add_to_pos = unit_vector_scaled(d, 200 / distance_to_player)
            self.pos = (self.pos[0] + int(add_to_pos[0]),
                        self.pos[1] + int(add_to_pos[1]))
        else:
            global game
            self.pos = (self.pos[0] - self.speed, self.pos[1] + math.sin(game.runtime))

        with self.canvas:
            Rectangle(pos=self.pos, size=self.size, group=self.group_name)

    def collision(self, pew):
        if pew.pos[0] + 30 < self.pos[0]: return False
        if pew.pos[0] + 30 > self.pos[0] + self.size[0]: return False
        if self.pos[1] < pew.pos[1] < self.pos[1] + self.size[1]: return True
        return False

    def destroy(self):
        self.pos = (-Window.size[0], 0)
        self.remove()

    def pygame_rect(self):
        return Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def points(self):
        if self.pos[0] > 0:
            return self.pos[0] * self.speed
        else:
            return 0

class Game(FloatLayout):
    # MAGIC!
    bezier_numbers = {
        '0': [[8, 2,  2, 2,  2, 12], [ 2, 12,  2, 22, 8, 22],
              [8, 2, 14, 2, 14, 12], [14, 12, 14, 22, 8, 22]],
        '1': [[8, 2, 8, 22], [8, 22, 6, 18]],
        '2': [[2, 17, 2, 22, 8, 22], [8, 22, 14, 22, 14, 17], [14, 17, 2, 2], [2, 2, 14, 2]],
        '3': [[2, 17, 2, 22, 8, 22], [8, 22, 14, 22, 14, 17], [14, 17, 14, 12, 8, 12],
              [2,  7, 2,  2, 8,  2], [8,  2, 14,  2, 14,  7], [14,  7, 14, 12, 8, 12]],
        '4': [[14, 2, 14, 22], [14, 22, 2, 10], [2, 10, 14, 10]],
        '5': [[14, 22, 2, 22], [2, 22, 2, 12], [2, 12, 10, 12],
              [2,  7, 2,  2, 8,  2], [8,  2, 14,  2, 14,  7], [14,  7, 14, 12, 10, 12]],
        '6': [[14, 22, 2, 22, 2, 7], [2, 7, 2, 2, 8, 2], [8, 2, 14, 2, 14, 7],
                                     [14, 7, 14, 12, 8, 12], [8, 12, 2, 12, 2, 7]],
        '7': [[2, 22, 14, 22], [14, 22, 8, 2]],
        '8': [[2, 17, 2, 22, 8, 22], [8, 22, 14, 22, 14, 17], [14, 17, 14, 12, 8, 12],
              [2,  7, 2,  2, 8,  2], [8,  2, 14,  2, 14,  7], [14,  7, 14, 12, 8, 12],
              [2,  7, 2, 12, 8, 12], [2, 17, 2, 12, 8, 12]],
        '9': [[2, 2, 14, 2, 14, 17], [14, 17, 14, 22, 8, 22], [8, 22, 2, 22, 2, 17],
                                     [2, 17, 2, 12, 8, 12], [8, 12, 14, 12, 14, 17]],
        'M': [[2, 2, 2, 22], [2, 22, 8, 12], [8, 12, 14, 22], [14, 22, 14, 2]],
        'V': [[2, 22, 8, 2], [8, 2, 14, 22]],
        'R': [[2, 2, 2, 22], [2, 22, 8, 22], [8, 22, 14, 22, 14, 17],
                                             [14, 17, 14, 12, 8, 12],
                                             [8, 12, 2, 12],
                                             [8, 12, 14, 2]],
        'T': [[2, 22, 14, 22], [8, 22, 8, 2]],
        'Y': [[2, 22, 8, 12], [14, 22, 8, 12], [8, 12, 8, 2]],
        'C': [[14, 17, 14, 22, 8, 22], [8, 22, 2, 22, 2, 12],
              [14,  7, 14,  2, 8,  2], [8,  2, 2,  2, 2, 12]],
        'L': [[2, 22, 2, 2], [2, 2, 14, 2]],
        'K': [[2, 2, 2, 22], [2, 12, 14, 2], [2, 12, 14, 22]],
    }

    SCORE_WHERE_TOPLEFT     = 0
    SCORE_WHERE_TOPRIGHT    = 1

    def on_touch_down(self, touch):
        if self.game_over:
            if touch.x < 16 * len("CL1CK 2 R3TRY") and touch.y > Window.size[1] - 24:
                self.reset_state()
            return

        self.touch_uids.append(touch.uid)
        if len(self.touch_uids) == 1:
            (self.last_touch_x, self.last_touch_y) = (touch.x, touch.y)
            return

        if len(self.touch_uids) != 2:
            # Only the second touch is a shoot
            return

        if self.last_pew + 0.3 > self.runtime:
            # Still cooling down the laser!
            return

        if len(self.pew_list) < 3:
            pew_pos = (self.player.pos[0] + self.player.size[0],
                       self.player.pos[1] + self.player.size[1] / 2)
            self.last_pew = self.runtime
            self.pew_list.append(Pew(self.canvas, pew_pos, str(self.runtime)))
            try:
                self.sounds['firing'].play()
            except KeyError:
                pass

    def on_touch_move(self, touch):
        if self.game_over: return

        if self.last_touch_x == None:
            return

        if self.touch_uids == []:
            return

        if self.touch_uids[0] != touch.uid:
            return

        for _ in range(int(touch.x - self.last_touch_x)): self.player.move_right()
        for _ in range(int(touch.y - self.last_touch_y)): self.player.move_down()
        for _ in range(int(self.last_touch_x - touch.x)): self.player.move_left()
        for _ in range(int(self.last_touch_y - touch.y)): self.player.move_up()
        (self.last_touch_x, self.last_touch_y) = (touch.x, touch.y)
        self.player.update(self.dt)

    def on_touch_up(self, touch):
        if self.game_over: return
        if self.touch_uids != []: self.touch_uids.remove(touch.uid)

    def draw_score(self, score, where=SCORE_WHERE_TOPLEFT):
        self.canvas.remove_group("score" + str(where))
        if where == self.SCORE_WHERE_TOPLEFT:
            shift = 0
        elif where == self.SCORE_WHERE_TOPRIGHT:
            shift = Window.size[0] - 16
            score = score[::-1]
        else:
            print "Unknown position for score: %d" % where
            return

        with self.canvas:
            for num in score:
                if num in self.bezier_numbers:
                    for bezier_points in self.bezier_numbers[num]:
                        bezier_points_shifted = []
                        for i in range(len(bezier_points)):
                            if i % 2 == 0:
                                bezier_points_shifted.append(bezier_points[i] + shift)
                            else:
                                bezier_points_shifted.append(Window.size[1] - 24 + bezier_points[i])
                        Bezier(points=bezier_points_shifted, group="score" + str(where))
                if where == self.SCORE_WHERE_TOPLEFT:
                    shift += 16
                elif where == self.SCORE_WHERE_TOPRIGHT:
                    shift -= 16
                else:
                    print "Unknown position for score: %d" % where
                    return

    def __init__(self):
        ret = super(Game, self).__init__()
        self.sounds = dict()
        self.sounds['firing'] = SoundLoader.load("sounds/firing.ogg")
        self.sounds['enemy_death'] = SoundLoader.load("sounds/enemy_death.ogg")
        self.sounds['game_over'] = SoundLoader.load("sounds/game_over.ogg")
        self.top_points = 0
        self.points = 0
        self.reset_state()
        return ret

    def reset_state(self):
        self.canvas.clear()
        self.dt = self.ticks = 0
        self.runtime = 0.0
        self.pew_list = []
        self.enemy_list = []
        self.last_pew = -10.0
        self.player = Player(60, self.canvas)
        self.player.update(self.dt)
        self.last_touch = None
        self.touch_uids = []
        self.game_over = False
        self.game_over_toogle = 0

        if self.points > self.top_points:
            self.top_points = self.points
        self.draw_score(str(self.top_points), where=self.SCORE_WHERE_TOPRIGHT)
        self.points = 0

        Clock.unschedule(self.toogle_score)
        Clock.schedule_interval(self.update, 1.0/60)
        self.draw_score(str(0))


    def update(self, dt):
        self.ticks += 1
        self.runtime += dt
        self.dt = dt

        if self.ticks % 120 == 0:
            print "Enemy list len: %d" % len(self.enemy_list)
            print "  Pew list len: %d" % len(self.pew_list)

        # Remove drawables that have disappeared from the screen
        self.pew_list = [x for x in self.pew_list if x.pos[0] < Window.size[0]]
        self.enemy_list = [x for x in self.enemy_list if x.pos[0] > -100]

        for pew in self.pew_list:
            pew.update(dt);

        for e in self.enemy_list:
            if self.player.collision(e.pygame_rect()):
                self.end_game()
                self.sounds['game_over'].play()
                self.game_over = True
                return

            for p in self.pew_list:
                if e.collision(p):
                    p.destroy()
                    self.points += e.points()
                    e.destroy()
                    self.draw_score(str(self.points))
                    self.sounds['enemy_death'].play()

        enemy_chance_inv = 100 - int(70 * math.atan(self.runtime / 60))
        if random.randint(0, enemy_chance_inv) == 0:
            self.enemy_list.append(Enemy(self.canvas, self.runtime))

        for e in self.enemy_list:
            e.update(dt, self.player.center_pos())

    def toogle_score(self, dt=0):
        if self.game_over_toogle % 4 == 0:
            self.draw_score("64M3 0V3R")
        elif self.game_over_toogle % 4 == 2:
            self.draw_score("CL1CK 2 R3TRY")
        else:
            self.draw_score(str(self.points))
        self.game_over_toogle += 1

    def end_game(self):
        Clock.unschedule(self.update)
        self.toogle_score()
        Clock.schedule_interval(self.toogle_score, 1)


class MyApp(App):
    def build(self):
        return game


if __name__ == '__main__':
    game = Game()
    MyApp().run()
