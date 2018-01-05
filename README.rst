csv_shp_viz
===========

A library that simplifies use of matplotlib, cartopy, descartes, etc. for
visualizing csv and shapefile geospatial data

Usage
-----

All relevant functions are documented in main.py. The main feature of
`csv_shp_viz` is the `styling` argument of `Visualizer.add_csv`, which
simplifies conditional coloring of geospatial data based on the values of
certain columns. The `styling` argument treats an array of dictionaries like an
if-else control flow, read from the first item of the array to the last item of
the array.

For example, the following Python code:

.. code-block:: python

    visualizer = Visualizer(
        bg_tiles = cartopy.io.img_tiles.StamenTerrain,
        zoom = 10
    )
    visualizer.add_shapefile(
        path = "./NYC.shp",
        border_color = "#ff0000",
        border_thickness = 1,
        fill_color = "none"
    )
    visualizer.add_csv(
        path = "./nyc_clusters.csv",
        lon_column = "longitude",
        lat_column = "latitude",
        main_column = "cluster",
        type = int,
        styling = [
            {
                "condition": lambda x: x == 1,
                "color": "#ff0000",
                "size": 0.5
            },
            {
                "condition": lambda x: x == 0,
                "color": "#0000ff",
                "size": 0.5
            },
            {
                "condition": lambda x: True,
                "color": "#000000",
                "size": 0.25
            }
        ]
    )
    visualizer.render()
    visualizer.show()

Can be translated into the following pseudocode:

::

    initialize visualizer, using StamenTerrain with zoom level 10 as background

    load shapes from ./NYC.shp:
        use color #ff0000 with thickness 1 to draw shape borders
        don't fill in shapes

    load points from ./nyc_clusters.csv:
        get longitudes from the longitude column
        get latitudes from the latitude column
        make comparisons on the cluster column, converted to int:
            if cluster == 1:
                use color #ff0000
                use size 0.5
            elif cluster == 0:
                use color #0000ff
                use size 0.5
            else:
                use color #000000
                use size 0.25

    render all layers
    show all layers

TODO
----

- YAML parser? It seems that yaml can more-or-less be parsed to kwargs for
  for the `add_shapefile` and `add_csv` functions
