#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Taken and customed from Jack Valmadre's Blog:
# http://jackvalmadre.wordpress.com/2008/09/21/resizable-image-control/
#
# Put together and created the time switching by Izidor Matusov <izidor.matusov@gmail.com>

import os, sys, time

import pygtk
pygtk.require('2.0')
import gtk
import glib
from stat import ST_CTIME, ST_MODE

def is_image(filename):
    """ File is image if it has a common suffix and it is a regular file """

    if not os.path.isfile(filename):
        return False

    if filename.lower().split('.')[-1] in ['jpg', 'png', 'bmp']:
        return True
    else:
        return False

def resizeToFit(image, frame, aspect=True, enlarge=False):
    """Resizes a rectangle to fit within another.

    Parameters:
    image -- A tuple of the original dimensions (width, height).
    frame -- A tuple of the target dimensions (width, height).
    aspect -- Maintain aspect ratio?
    enlarge -- Allow image to be scaled up?

    """
    if aspect:
        return scaleToFit(image, frame, enlarge)
    else:
        return stretchToFit(image, frame, enlarge)

def scaleToFit(image, frame, enlarge=False):
    image_width, image_height = image
    frame_width, frame_height = frame
    image_aspect = float(image_width) / image_height
    frame_aspect = float(frame_width) / frame_height
    # Determine maximum width/height (prevent up-scaling).
    if not enlarge:
        max_width = min(frame_width, image_width)
        max_height = min(frame_height, image_height)
    else:
        max_width = frame_width
        max_height = frame_height
    # Frame is wider than image.
    if frame_aspect > image_aspect:
        height = max_height
        width = int(height * image_aspect)
    # Frame is taller than image.
    else:
        width = max_width
        height = int(width / image_aspect)
    return (width, height)

def stretchToFit(image, frame, enlarge=False):
    image_width, image_height = image
    frame_width, frame_height = frame
    # Stop image from being blown up.
    if not enlarge:
        width = min(frame_width, image_width)
        height = min(frame_height, image_height)
    else:
        width = frame_width
        height = frame_height
    return (width, height)


class ResizableImage(gtk.DrawingArea):

    def __init__(self, aspect=True, enlarge=False,
            interp=gtk.gdk.INTERP_NEAREST, backcolor=None, max=(1600,1200)):
        """Construct a ResizableImage control.

        Parameters:
        aspect -- Maintain aspect ratio?
        enlarge -- Allow image to be scaled up?
        interp -- Method of interpolation to be used.
        backcolor -- Tuple (R, G, B) with values ranging from 0 to 1,
            or None for transparent.
        max -- Max dimensions for internal image (width, height).

        """
        super(ResizableImage, self).__init__()
        self.pixbuf = None
        self.aspect = aspect
        self.enlarge = enlarge
        self.interp = interp
        self.backcolor = backcolor
        self.max = max
        self.connect('expose_event', self.expose)
        self.connect('realize', self.on_realize)

    def on_realize(self, widget):
        if self.backcolor is None:
            color = gtk.gdk.Color()
        else:
            color = gtk.gdk.Color(*self.backcolor)

        self.window.set_background(color)

    def expose(self, widget, event):
        # Load Cairo drawing context.
        self.context = self.window.cairo_create()
        # Set a clip region.
        self.context.rectangle(
            event.area.x, event.area.y,
            event.area.width, event.area.height)
        self.context.clip()
        # Render image.
        self.draw(self.context)
        return False

    def draw(self, context):
        # Get dimensions.
        rect = self.get_allocation()
        x, y = rect.x, rect.y
        # Remove parent offset, if any.
        parent = self.get_parent()
        if parent:
            offset = parent.get_allocation()
            x -= offset.x
            y -= offset.y
        # Fill background color.
        if self.backcolor:
            context.rectangle(x, y, rect.width, rect.height)
            context.set_source_rgb(*self.backcolor)
            context.fill_preserve()
        # Check if there is an image.
        if not self.pixbuf:
            return
        width, height = resizeToFit(
            (self.pixbuf.get_width(), self.pixbuf.get_height()),
            (rect.width, rect.height),
            self.aspect,
            self.enlarge)
        x = x + (rect.width - width) / 2
        y = y + (rect.height - height) / 2
        context.set_source_pixbuf(
            self.pixbuf.scale_simple(width, height, self.interp), x, y)
        context.paint()

    def set_from_pixbuf(self, pixbuf):
        width, height = pixbuf.get_width(), pixbuf.get_height()
        # Limit size of internal pixbuf to increase speed.
        if not self.max or (width < self.max[0] and height < self.max[1]):
            self.pixbuf = pixbuf
        else:
            width, height = resizeToFit((width, height), self.max)
            self.pixbuf = pixbuf.scale_simple(
                width, height,
                gtk.gdk.INTERP_BILINEAR)
        self.invalidate()

    def set_from_file(self, filename):
        self.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(filename))

    def invalidate(self):
        self.queue_draw()

class DemoGtk:

    SECONDS_BETWEEN_PICTURES = 3
    FULLSCREEN = True
    WALK_INSTEAD_LISTDIR = True     # this option can be used to list only one layer images
    IMAGES_LIMIT = 20       # how many images will be put in the slides

    def __init__(self):
        self.window = gtk.Window()
        self.window.connect('destroy', gtk.main_quit)
        self.window.set_title('DirectPYQ')

        self.image = ResizableImage( True, True, gtk.gdk.INTERP_BILINEAR)
        self.image.show()
        self.window.add(self.image)

        self.load_file_list()


        self.window.show_all()

        if self.FULLSCREEN:
            self.window.fullscreen() 

        glib.timeout_add_seconds(self.SECONDS_BETWEEN_PICTURES, self.on_tick)
        self.display()

    def load_file_list(self):
        """ Find all images """
        self.files = []
        file_entries = []
        self.index = 0

        for directory, sub_directories, files in os.walk('./mail'):
            for filename in files:
                filepath = os.path.join(directory, filename)
                if is_image(filepath):
                    file_entries.append((os.stat(filepath), filepath))
            file_entries = [(stat[ST_CTIME], path) for stat, path in file_entries]
            file_entries = sorted(file_entries, reverse=True)
            
        self.files = [entry[1] for entry in file_entries[0:min(self.IMAGES_LIMIT, len(file_entries))]]
        print time.time(), "Reload iamge list"

        
    def display(self):
        """ Sent a request to change picture if it is possible """
        if 0 <= self.index < len(self.files):
            self.image.set_from_file(self.files[self.index])
            return True
        else:
            return False

    def on_tick(self):
        """ Skip to another picture.

        If this picture is last, reload file list and
        show up slides in decreasing chronologically order. 
        """
        self.index += 1
        if self.index >= len(self.files):
            self.load_file_list()
            self.index = 0

        return self.display()

if __name__ == "__main__":
    gui = DemoGtk()
    gtk.main()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4