"""
This module contains code useful for plotting the stock graphs and caching the datasets used to generate them.
"""
import os.path

from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from werkzeug.contrib.cache import FileSystemCache

from google_data_source import get_google_data_for_stock

# get the full path of the directory of the application
app_root = os.path.abspath(os.path.dirname(__file__))

# set up the cache directory as the subdirectory 'cache'
CACHE_DIR = os.path.join(app_root, 'cache')

# set the expiry of each object in the cache to 1 day (24 hrs) as this is what one datapoint of the datasets represents,
# so the data won't be out of date for at least a day after
EXPIRY_SECONDS = 24 * 60 * 60  # HOURS * MINUTES * SECONDS

# create the werkzeug cache object with the cache directory and expiry
cache = FileSystemCache(CACHE_DIR, default_timeout=EXPIRY_SECONDS, threshold=100) # threshold = 100 -> after 100 items stored, cache begins deleting some even if not yet expired


def plot_stocks(graph_pane_collection, stock1, stock2, time_periods):
    """
    Plots new graphs for stock1 and stock2 at each of the time_periods on the graphs in graph_pane_collection.

    :param graph_pane_collection: The graph panes to draw the new graphs on.
    :param stock1: The details of stock 1
    :param stock2: The details of stock 2
    :param time_periods: a list of time periods to plot these stocks on
    :return: Boolean, True if successful, False otherwise
    """
    data_frames_stock1 = []
    data_frames_stock2 = []

    # iterate through each time period
    for tp in time_periods:
        # determine the key in cache for stock 1
        cache_key_stock1 = "{0}:{1}.{2}".format(
            stock1.get('gf_code'),
            stock1.get('gf_index'),
            tp
        )

        # determine the key in cache for stock 2
        cache_key_stock2 = "{0}:{1}.{2}".format(
            stock2.get('gf_code'),
            stock2.get('gf_index'),
            tp
        )

        # check if there is anything in cache for stock 1 key
        if cache.get(cache_key_stock1) is not None:
            # if so, use it
            data_frames_stock1.append(cache.get(cache_key_stock1))
        else:
            # fetch new data from google
            try:
                df_1 = get_google_data_for_stock(stock1.get('gf_code'), stock1.get('gf_index'), interval_seconds=86400, period=tp)
                data_frames_stock1.append(df_1)
                cache.set(cache_key_stock1, df_1)  # cache the new data
            except ValueError:
                # stock data invalid, error
                return False

        # check if there is anything in cache for stock 2 key
        if cache.get(cache_key_stock2) is not None:
            # if so, use it
            data_frames_stock2.append(cache.get(cache_key_stock2))
        else:
            # fetch new data from google
            try:
                df_2 = get_google_data_for_stock(stock2.get('gf_code'), stock2.get('gf_index'), interval_seconds=86400, period=tp)
                data_frames_stock2.append(df_2)
                cache.set(cache_key_stock2, df_2)  # cache the new data
            except ValueError:
                # stock data invalid, error
                return False

    # iterate through each graph pane and draw the graph on each
    for idx, pane in enumerate(graph_pane_collection.graphs):
        # get the datafram for stock 1
        df1 = data_frames_stock1[idx]

        # extract the x and y values to a tuple
        stock_1_data = (df1.index, df1.Close)

        # get the datafram for stock 2
        df2 = data_frames_stock2[idx]

        # extract the x and y values to a tuple
        stock_2_data = (df2.index, df2.Close)

        # set the time period associated with this graph pane
        pane.time_period = time_periods[idx]

        # draw the new graph data
        pane.draw(stock_1_data, stock_2_data)

    # return true if all went successfully
    return True


class GraphCanvas(FigureCanvas):
    """
    GraphCanvas can be used as a widget for a matplotlib graph.
    """
    def __init__(self, parent=None, width=7, height=7, dpi=60):
        """
        Constructor for GraphCanvas.

        :param parent: Parent widget
        :param width: Width of matplotlib graph
        :param height: Height of matplotlib graph
        :param dpi: DPI (Dots Per Inch) of graph
        """
        figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = figure.add_subplot(111)

        FigureCanvas.__init__(self, figure)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def update_lines(self, line1, line2, title):
        """
        Update the graph with new lines to draw, and a new title.

        :param line1: The first series to draw.
        :param line2: The second series to draw.
        :param title: The new title of the graph
        :return: None
        """
        # clear the axes
        self.axes.cla()

        # plot stock 1
        self.axes.plot_date(line1[0], line1[1], xdate=True, ydate=False, linestyle='solid')

        # plot stock 2
        self.axes.plot_date(line2[0], line2[1], xdate=True, ydate=False, linestyle='solid')

        # set the new graph titile
        self.axes.set_title(title)

        # format the x axis labels so that there are no overlaps
        self.figure.autofmt_xdate()

        # draw the new graph
        self.draw()


class GraphPane(QVBoxLayout):
    """
    GraphPane is a view of a graph and details about the change in price of a stock since open and close,
    and which stock is best.
    """
    def __init__(self, model, time_period='1M'):
        """
        Constructor for GraphPane
        :param model: ConfigurationModel for the pane to read from.
        :param time_period: The time period to be shown on the pane's graph.
        """
        super().__init__()
        self.model = model
        self.time_period = time_period

        # create a layout for the change in price and best info
        meta_box = QHBoxLayout()

        # create a VBox layout for the differences in stocks 1 and 2
        diffs_box = QVBoxLayout()

        # create a layout, label and output label for the change in stock 1
        stock1_change = QHBoxLayout()
        stock1_change.addWidget(QLabel('Change in Stock 1:'))
        self.stock1_change_label = QLabel('')
        stock1_change.addWidget(self.stock1_change_label)
        diffs_box.addLayout(stock1_change)

        # create a layout, label and output label for the change in stock 2
        stock2_change = QHBoxLayout()
        stock2_change.addWidget(QLabel('Change in Stock 2:'))
        self.stock2_change_label = QLabel('')
        stock2_change.addWidget(self.stock2_change_label)
        diffs_box.addLayout(stock2_change)

        # add the 'differences' layout to the larger stock price metadata layout
        meta_box.addLayout(diffs_box)

        # create a layout for the 'best' stock with label and output label
        best = QHBoxLayout()
        best.addWidget(QLabel('BEST:'))
        self.best_label = QLabel('')
        best.addWidget(self.best_label)
        meta_box.addLayout(best)

        # add the metadata layout to the graph pane
        self.addLayout(meta_box)

        # add the actual graph canvas to the pane
        self.graph_canvas = GraphCanvas()
        self.addWidget(self.graph_canvas)

    def draw(self, line1, line2):
        """
        Updates the GraphPane with the new lines line1 and line2
        and calculates difference in open and close for each stock
        and then decided which is best and displays this information on the relevant output labels

        :param line1: The line data for stock 1
        :param line2: The line data for stock 2
        :return: None
        """

        # draw the new lines
        self.graph_canvas.update_lines(line1, line2, self.time_period)

        # get the open and close values for stock 1
        stock1_open = line1[1][0]
        stock1_close = line1[1][-1]

        # get the open and close values for stock 2
        stock2_open = line2[1][0]
        stock2_close = line2[1][-1]

        # calculate the difference in open and close
        diff_1 = stock1_close - stock1_open
        diff_2 = stock2_close - stock2_open

        # calculate the percentage change since open for both stocks
        per_change_1 = (float(diff_1) / stock1_open) * 100
        per_change_2 = (float(diff_2) / stock2_open) * 100

        # determine which sign to use depending on if the percentage change is positive or negative
        sign_1 = '+' if per_change_1 >= 0 else '-'
        sign_2 = '+' if per_change_2 >= 0 else '-'

        # set the stock 1 output label to show the difference and percentage change
        self.stock1_change_label.setText("{sign}{0:.2f} {sign}{1:.2f}%".format(abs(diff_1), abs(per_change_1), sign=sign_1))
        self.stock1_change_label.setStyleSheet('color: {0}'.format('green' if per_change_1 >= 0 else 'red'))

        # set the stock 2 ouptut label to show the difference and percentage change
        self.stock2_change_label.setText("{sign}{0:.2f} {sign}{1:.2f}%".format(abs(diff_2), abs(per_change_2), sign=sign_2))
        self.stock2_change_label.setStyleSheet('color: {0}'.format('green' if per_change_2 >= 0 else 'red'))

        # determine wich is best
        if per_change_1 == per_change_2:
            # if the same percentage change (very rare, but possible) then neither are better

            # update the best output label to show neither
            self.best_label.setText('NEITHER')
            self.best_label.setStyleSheet('color: black')
        elif per_change_1 > per_change_2:
            # if the percentage change of stock 1 is greater than that of stock 2, stock 1 is better

            # update the best output label to show stock 1 being better
            self.best_label.setText(self.model.stock_1_code)
            self.best_label.setStyleSheet('color: blue')  # colour chosen by matplotlib for series 1
        else:
            # finally, if the percentage change of stock 2 is greater than that of stock 1, stock 2 is better

            # update the best output label to show stock 2 being better
            self.best_label.setText(self.model.stock_2_code)
            self.best_label.setStyleSheet('color: green')  # colour chosen by matplotlib for series 2
