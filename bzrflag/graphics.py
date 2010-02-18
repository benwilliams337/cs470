'''Graphics module:
    handles all graphics; here are defined the base
classes for various graphics implementations to subclass

NOTE:
    to find the pygame implementation, look in modpygame.py

'''

import math
import pygame
import constants
import config
from world import Base, Box
from game import Tank, Shot, Flag, Base

import os

DEFAULT_SIZE = 700, 700

DATA_DIR = os.path.abspath(os.path.join(
        os.path.split(__file__)[0], '..', 'data'))
GROUND = 'std_ground.png'
WALL = 'wall.png'
BASE_PATTERN = '%s_basetop.png'
SHOT_PATTERN = '%s_bolt.png'
FLAG_PATTERN = '%s_flag.png'
TANK_PATTERN = '%s_tank.png'
TILESCALE = 0.1
SHOTSCALE = 2
FLAGSCALE = 3
TANKSCALE = 1.2

class ImageCache(object):
    def __init__(self):
        self._ground = None
        self._wall = None

        self.suffixes = {'base':'basetop','shot':'bolt','tank':'tank','flag':'flag'}
        ## curently lazy loading...is that good?
        self._teamcache = {'base':{},'shot':{},'flag':{},'tank':{}}
        self._cache = {}

    def ground(self):
        """Creates a surface of the ground image.

        The surface is scaled down using the factor in TILESCALE.
        """
        if not self._cache.has_key('ground'):
            ground = self.load_image(GROUND)
            self._ground = self.scaled_image(ground, TILESCALE)
        return self._ground

    def wall(self):
        """Returns a surface for walls.

        The surface is scaled down using the factor in TILESCALE.
        """
        if not self._wall:
            wall = self.load_image(WALL)
            self._wall = self.scaled_image(wall, TILESCALE)
        return self._wall

    def loadteam(self, type, color):
        if not self._teamcache.has_key(type):
            raise KeyError,"invalid image type: %s"%type
        if not color in constants.COLORNAME:
            raise KeyError,"invalid color: %s"%color
        if not self._teamcache[type].has_key(color):
            self._teamcache[type][color] = self.load_image('%s_%s.png'%(color,self.suffixes[type]))
        return self._teamcache[type][color]

    def scaled_size(self, size, scale):
        """Scales a size (width-height pair).

        If the scale is None, scaled_size returns the original size unmodified.
        """
        if scale is not None:
            w, h = size
            w = int(round(w * scale))
            h = int(round(h * scale))
            size = w, h
        return size

    def load_image(self, filename):
        """Loads the image with the given filename from the DATA_DIR."""
        raise Exception,'override this method'

    def scaled_image(self, image, scale):
        """Scales the given image to the given size."""
        raise Exception,'override this method'

    def tile(self, tile, size):
        """Creates a surface of the given size tiled with the given surface."""
        raise Exception,'override this method'


class BZSprite(pygame.sprite.Sprite):
    """Determines how a single object in the game will be drawn.

    The sprite manager uses the sprite's `image` and `rect` attributes to draw
    it.
    """

    def __init__(self, bzobject, image, display, otype=None):
        super(BZSprite, self).__init__()

        self.bzobject = bzobject
        self.display = display
        self.orig_image = image
        self.image = None
        self.type = otype

        self.rect = image.get_rect()
        self.prev_rot = None
        self.prev_scale = None

        self.update(True)

    def object_size(self):
        """Finds the screen size of the original unrotated bzobject."""
        return self.display.size_world_to_screen(self.bzobject.size)

    def _translate(self):
        """Translates the image to the bzobject's position."""

        self.rect.center = self.display.pos_world_to_screen(self.bzobject.pos)

    def _render_image(self, image, scale):
        raise Exception,'_scale_image must be overridden'

    def update(self, force=False):
        """Overrideable function for creating the image.

        If force is specified, the image should be redrawn even if the
        bzobject doesn't appear to have changed.
        """
        rot = self.bzobject.rot

        '''if force or (rot != self.prev_rot):
            self.prev_rot = rot
            self.image = self.orig_image
            if rot:
                self._rotate()
                self._scale_rotated()
            else:
                self._scale_prerotated()'''
        self._render_image()
        self.rect = self.image.get_rect()
        self._translate()

class Display(object):
    """Manages all graphics."""
    _imagecache = ImageCache
    _spriteclass = BZSprite
    def __init__(self, game, screen_size=(700,700)):
        self.game = game
        self.world = config.config.world
        self.screen_size = screen_size
        self.images = self._imagecache()
        self._background = None
        self.spritemap = {}
        self.scale = 1
        self.pos = [0,0]

    def setup(self):
        """Initializes and creates the screen surface."""
        pass

    def update(self):
        """Updates the state of all sprites and redraws the screen."""
        pass

    def pos_world_to_screen(self, pos):
        """Converts a position from world space to screen pixel space.

        >>> pos_world_to_screen((0, 0), (800, 800), (400, 400))
        (200, 200)
        >>> pos_world_to_screen((-400, -400), (800, 800), (400, 400))
        (0, 400)
        >>>
        """
        x, y = pos
        world_width, world_height = self.world.size
        x += world_width / 2
        y -= world_height / 2
        x, y = self.vec_world_to_screen((x, y))
        return x+self.pos[0], y+self.pos[1]

    def size_world_to_screen(self, size):
        """Converts sizes from BZFlag world space to screen space.

        Note that bzflag sizes are more like a radius (half of width), so we
        double them to normalize.
        """
        w, h = size
        w *= 2
        h *= -2
        screen_size = self.vec_world_to_screen((w, h))
        return screen_size

    def vec_world_to_screen(self, vector):
        """Converts a vector from world space to screen pixel space.

        >>> vec_world_to_screen((200, 200), (800, 800), (400, 400))
        (100, -100)
        >>>
        """
        wscale,hscale = self.world_to_screen_scale()

        x, y = vector
        return int(round(x * wscale)), -int(round(y * hscale))

    def world_to_screen_scale(self):
        screen_width, screen_height = self.screen_size
        world_width, world_height = self.world.size
        wscale = screen_width / float(world_width) * self.scale
        hscale = screen_height / float(world_height) * self.scale
        return wscale, hscale

    def add_object(self, obj):
        types = (Tank, 'tank'),(Shot,'shot'),(Flag,'flag'),(Base,'base')
        otype = None
        for cls,name in types:
            if isinstance(obj,cls):
                otype = name
                break
        else:
            raise Exception,'invalid object added to display: %s'%obj
        #print 'adding',otype,'at pos',obj.pos,'translated to',self.pos_world_to_screen(obj.pos)
        #print self.world.size,self.screen_size
        image = self.images.loadteam(otype, obj.team.color)
        sprite = self._spriteclass(obj, image, self, otype)
        self.add_sprite(sprite, otype)
        self.spritemap[obj] = sprite

    def remove_object(self, obj):
        self.remove_sprite(self.spritemap[obj])

    def add_sprite(self,sprite,otype):
        raise Exception,'add_sprite must be overridden'

    def remove_sprite(self, sprite):
        raise Exception,'remove_sprite must be overridden'
