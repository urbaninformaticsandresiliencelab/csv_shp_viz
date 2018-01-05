#!/usr/bin/env python3

import matplotlib.pyplot
import cartopy.crs
import cartopy.io.img_tiles
import csv
import descartes
import fiona
import shapely.geometry
import sys

class Visualizer(object):

    def __init__(self, bg_tiles = None, zoom = 10):
        """ Initializes Visualizer class

        Args:
            bg_tiles: A class descending from cartopy.io.img_tiles.GoogleTiles
            zoom: The zoom level to use for the bg_tiles instance

        Layers are dictionaries that are guaranteed to have the following
        indices:
            path: The path of a layer
            type: "csv" or "shapes"
            extents: array of size 4, containing min_x, min_y, max_x, max_y
        """
        self.layers = []

        if (bg_tiles):
            print("loading tiles: %s" % (bg_tiles))
            tiles = bg_tiles()

            self.point_transform = cartopy.crs.Geodetic()
            self.polygon_transform = cartopy.crs.PlateCarree()
            self.axis = matplotlib.pyplot.axes(projection = tiles.crs)

            self.axis.add_image(tiles, zoom)

        else:
            self.point_transform = None
            self.polygon_transform = None
            self.axis = matplotlib.pyplot.axes()

    def add_shapefile(
        self, path, border_color, fill_color,
        border_thickness = 1
    ):
        """ Adds a shapefile layer

        Args:
            path: The path of the .shp file
            border_color: The color to use for shape borders
            fill_color: The color to use for shape fills
            border_thickness: The thickness of shape borders

        layer structure:
        {
            "path": the shapefile's path
            "type": "shapes",
            "extents": array of size 4, containing min_x, min_y, max_x, max_y
            "shapes": [
                {
                    "shape": object produced by shapely.geometry.shape
                    "kwargs": keyword args to be passed to descartes.PolygonPatch
                }
            ]
        }

        """

        layer = {
            "path": path,
            "type": "shapes",
            "extents": None,
        }
        shapes = []

        i = 0
        with fiona.drivers():
            with fiona.open(path) as source:
                for record in source:
                    shape = shapely.geometry.shape(record["geometry"])
                    bounds = shape.bounds

                    if (layer["extents"]):
                        for i in range(4):
                            if (i <= 1):
                                f = min
                            else:
                                f = max
                            layer["extents"][i] = f([
                                layer["extents"][i], bounds[i]
                            ])
                    else:
                        layer["extents"] = list(bounds)

                    shapes.append({
                        "shape": shape,
                        "kwargs": {
                            "facecolor": fill_color,
                            "edgecolor": border_color,
                            "linewidth": border_thickness
                        }
                    })

                    i += 1
                    sys.stdout.write("\rloaded %s:%d" % (path, i))
                    sys.stdout.flush()
        print("")

        layer["shapes"] = shapes
        self.layers.append(layer)

    def add_csv(
        self, path, lon_column, lat_column, main_column, styling,
        type = int, marker = ","
    ):
        """ Adds csv layer

        Args:
            path: The path of the CSV to load
            lon_column: The name of the column containing the longitude
                coordinates
            lat_column: The name of the column containing the latitude
                coordinates
            main_column: The column containing the data to be used to color the
                visualization
            type: The type that columns in the main column should be converted
                to before being run through comparisons
            marker: The matplotlib marker type to use
            styling: An array of dictionaries, structured as such:

                {
                    "condition": A function that returns True on a certain
                        condition
                    "color": A string corresponding to a hex value to be used
                        if the condition passes
                    "size": A float corresponding to the size to be used if the
                        condition passes
                }

                for example:

                {
                    "condition": lambda x: x == 1,
                    "color": "#ff0000",
                    "size": 0.5
                },
                {
                    "condition": lambda x: x == 1,
                    "color": "#0000ff",
                    "size": 0.5
                },
                {
                    "condition": lambda x: True,
                    "color": "#000000",
                    "size": 0.5
                }

        styling is treated as an if-else control flow, from top to bottom.
        The example above can be considered as the following pseudocode:

            if main_column == 1:
                color = #ff0000
                size = 0.5
            elif main_column == 1:
                color = #0000ff
                size = 0.5
            else:                           # lambda x: True always returns True
                color = #000000
                size

        Layer structure:
        {
            "path": the csv's path
            "type": "csv"
            "kwargs": kwargs to be passed to axis.scatter
        }

        """

        layer = {
            "path": path,
            "type": "csv"
        }
        kwargs = {
            "x": [],
            "y": [],
            "c": [],
            "s": [],
            "marker": marker
        }

        i = 0
        with open(path, "r") as f:
            for row in csv.DictReader(f):
                value = type(row[main_column])

                for style in styling:
                    if (style["condition"](value)):
                        kwargs["x"].append(float(row[lon_column]))
                        kwargs["y"].append(float(row[lat_column]))
                        kwargs["c"].append(style["color"])
                        kwargs["s"].append(style["size"])
                        break

                i += 1
                sys.stdout.write("\rloaded %s:%d" % (path, i))
                sys.stdout.flush()
        print("")

        layer["kwargs"] = kwargs
        layer["extents"] = [
            min(kwargs["x"]),
            min(kwargs["y"]),
            max(kwargs["x"]),
            max(kwargs["y"])
        ]
        self.layers.append(layer)

    def render(self):
        """ Renders all layers and sets the extents be the most extreme points
        found across all layers """

        all_x = []
        all_y = []
        z = 0

        for layer in self.layers:
            z += 1
            print("rendering %s" % layer["path"])

            if (layer["type"] == "csv"):
                kwargs = layer["kwargs"]
                kwargs["zorder"] = z
                kwargs["lw"] = 0

                if (self.point_transform):
                    kwargs["transform"] = self.point_transform

                self.axis.scatter(**kwargs)

            elif (layer["type"] == "shapes"):
                for shape in layer["shapes"]:
                    kwargs = shape["kwargs"]
                    kwargs["zorder"] = z

                    patch = descartes.PolygonPatch(
                        shape["shape"],
                        **kwargs
                    )

                    if (self.polygon_transform):
                        patch.set_transform(self.polygon_transform)

                    self.axis.add_patch(patch)

            all_x.append(layer["extents"][0])
            all_y.append(layer["extents"][1])
            all_x.append(layer["extents"][2])
            all_y.append(layer["extents"][3])

        self.axis.set_extent([
            min(all_x), max(all_x), min(all_y), max(all_y)
        ])

    def set_extents(min_x, max_x, min_y, max_y):
        """ Overrides extents set by self.render; must be run AFTER self.render
        """

        self.axis.set_extent([min_x, max_x, min_y, max_y])

    def use_extents(path):
        """ Use the extents of the given layer

        Args:
            path: The path of an already-loaded layer
        """

        for layer in self.layers:
            if (layer["path"] == path):
                self.axis.set_extent(layer["extents"])
                break

    def show(self):
        matplotlib.pyplot.show()

    def savefig(self, *args, **kwargs):
        matplotlib.pyplot.savefig(*args, **kwargs)
