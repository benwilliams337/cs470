#!/usr/bin/env python

"""
README

This should get some of the boilerplate out of the way for you in visualizing
your potential fields.

Notably absent from this code is anything dealing with vectors, the
interaction of mutliple fields, etc. Your code will be a lot easier if you
define your potential fields in terms of vectors (angle, magnitude). For
plotting, however, you'll need to turn them back into dx and dy.
"""


import matplotlib.pyplot as plt
from pylab import *
import math
import random

from math import atan2, cos, sin, sqrt, pi


##### PLOTTING FUNCTIONS #####


def show_obstacle(plot, points):
    """Draw a polygon. Points is a list if [x,y] tuples
    """
    for p1, p2 in zip(points, [points[-1]] + list(points)):
        plot.plot([p1[0], p2[0]], [p1[1], p2[1]], 'b')


def show_arrows(plot, potential_func, xlim=(-400, 400), ylim=(-400, 400), res=20):
    """
    Arguments:
        fns: a list of potential field functions
        xlim, ylim: the limits of the plot
        res: resolution for (spacing between) arrows
    """
    plot.set_xlim(xlim)
    plot.set_ylim(ylim)
    for x in range(xlim[0], xlim[1] + res, res):
        for y in range(ylim[0], ylim[1] + res, res):
            dx, dy = potential_func(x, y, res)
            if dx + dy == 0: continue
            plot.arrow(x, y, dx, dy, head_width=res/7.0, color='red', linewidth=.3)


def plot_single(potential_func, obstacles, filename, xlim=(-400, 400), ylim=(-400, 400)):
    """Plot a potential function and some obstacles, and write the resulting
    image to a file"""
    print "Generating", filename
    fig = plt.figure()
    plot = plt.subplot(111)
    show_arrows(plot, potential_func, xlim=xlim, ylim=ylim)
    for obstacle in obstacles:
        show_obstacle(plot, obstacle)
    fig.savefig(filename, format='png')


#### TRIVIAL EXAMPLE FUNCTIONS ####


def random_field(x, y, res):
    """
    NOTE: Your potential field calculator should probably work in vectors
    (angle, magnitude), but you need to return dx, dy for plotting.

    Arguments:
        x:   the x position for which to calculate the potential field
        y:   the y position for which to calculate the potential field
        res: current plotting resolution (helpful for scaling down your
             vectors for display, so they don't all overlap each other)

    Returns:
        dx, dy: the change in x and y for the arrow to point.
    """

    return random.randint(-res, res), random.randint(-res, res)


def unidirectional(x, y, res):
    """Another simple example"""

    return res, res/2


def bidirectional(x, y, res):
    if x > 0:
        return res, res/2
    else:
        return -res, res/2


def main():
    triangle = ((0, 0), (100, 100), (-100, 50))
    plot_single(random_field, [triangle], 'random.png')
    plot_single(unidirectional, [triangle], 'unidirectional.png')
    plot_single(bidirectional, [triangle], 'bidirectional.png')


if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
