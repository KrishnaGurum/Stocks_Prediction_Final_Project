"""
The main file of the Stock Prediction application. MainWindow class defined here.

"""
import json
import sys

import matplotlib
matplotlib.use("Qt5Agg")  # use the Qt5 Aggregator for plotting matplotlib graphs to the Qt GUI

from PyQt5.QtWidgets import *

from plot import GraphPane
from widgets import StockSelector, TimePeriodsChooser, PlotStockButton


class ConfigurationModel:
    """
    Abstraction for the last used configuration (stock names and time periods)
    """
    def __init__(self):
        self.stock_1_code = ""
        self.stock_1_index = ""
        self.stock_2_code = ""
        self.stock_2_index = ""
        self.time_periods = []

    def load(self):
        """
        Loads the configuration from the file located in the same directory called 'config.json'

        :return: None
        """
        try:
            with open('config.json', 'r') as file:
                json_dict = json.load(file)

            self.stock_1_code = json_dict['stock_1']['code']
            self.stock_1_index = json_dict['stock_1']['index']
            self.stock_2_code = json_dict['stock_2']['code']
            self.stock_2_index = json_dict['stock_2']['index']
            self.time_periods = json_dict['time_periods']
        except FileNotFoundError:
            print('no config file found')

    def save(self):
        """
        Saves the configuration to the file located in the same directory called 'config.json'

        :return: None
        """
        json_dict = {
            'stock_1': {
                'code': self.stock_1_code,
                'index': self.stock_1_index
            },
            'stock_2': {
                'code': self.stock_2_code,
                'index': self.stock_2_index
            },
            'time_periods': self.time_periods
        }
        with open('config.json', 'w+') as file:
            json.dump(json_dict, file)  # serialize as json and save


class GraphPaneCollection(QHBoxLayout):
    """
    Layout to hold multiple graph panes to show graphs with different time periods and information about those stocks.
    """
    def __init__(self, n_graphs, model):
        """
        Constructor for GraphPaneCollection.

        Initializes a GraphPaneCollection with n_graphs objects of type GraphPane.

        :param n_graphs: The number of 'GraphPane'(s) to create.
        :param model: The ConfigurationModel to use when updating GraphPanes.
        """
        super().__init__()

        self.graphs = []
        self.model = model

        for _ in range(n_graphs):
            gp = GraphPane(model)
            self.graphs.append(gp)
            self.addLayout(gp)  # add the graph pane to the current layout


class ApplicationWindow(QMainWindow):
    """
    Class representing the main application window that all other windows and widgets have as a parent.
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor for ApplicationWindow.

        Initializes the QMainWindow base class, loads the app's ConfigurationModel
        and then invokes init_ui to set up our application's widgets.

        :param args: positional arguments to pass to the QMainWindow constructor
        :param kwargs: keyword arguments to pass to the QMainWindow constructor
        """
        super().__init__(*args, **kwargs)

        # set the number of graphs the application will display
        self.n_graphs = 3

        # set up the configuration model and load from file (if possible)
        self.model = ConfigurationModel()
        self.model.load()

        # create the widgets for this application.
        self.init_ui()

    def init_ui(self):
        """
        Method called during object construction to set up our application's widgets.

        :return: None
        """

        # set window size and title
        self.setGeometry(300, 300, 800, 800)
        self.setWindowTitle('Stocks Visualising')

        # set up 'exit' action
        exit_Action = QAction('Exit', self)
        exit_Action.setShortcut('Ctrl + Q')
        exit_Action.setStatusTip('Exit from Application')
        exit_Action.triggered.connect(self.close)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exit_Action)

        # create a main widget to act as a parent for all other widgets
        mainWidget = QWidget()

        # create the main layout of the application to be a VBox layout
        layout = QVBoxLayout()

        # ==== APP LAYOUT SECTIONS HERE ====

        # Add stock choosers for stocks 1 and 2
        stock_1_chooser = StockSelector(1, self.model)
        stock_2_chooser = StockSelector(2, self.model)

        layout.addLayout(stock_1_chooser)
        layout.addLayout(stock_2_chooser)

        # add a time period chooser
        time_period_chooser = TimePeriodsChooser(self.n_graphs, self.model)
        layout.addLayout(time_period_chooser)

        # create the graph pane collection (but don't add, we want this below the plot stock button defined below)
        graph_pane_collection = GraphPaneCollection(self.n_graphs, self.model)

        # create and add the plot stock button (which references the graph_pane_collection)
        plot_stock_button = PlotStockButton(graph_pane_collection, time_period_chooser, stock_1_chooser, stock_2_chooser)
        layout.addWidget(plot_stock_button)

        # add the graph pane collection, created above, to the layout
        layout.addLayout(graph_pane_collection)

        # === END APP LAYOUT SECTIONS ====

        # set the layout of the parent widget to the application layout we have created
        mainWidget.setLayout(layout)

        # set the app's central widget to said parent widget
        self.setCentralWidget(mainWidget)


if __name__ == '__main__':
    # if we are executing this file...

    # create a QApplication
    app = QApplication(sys.argv)

    # create an Application Window
    a_Window = ApplicationWindow()

    # enable one of the following:
    a_Window.show()
    # window.showFullScreen()

    # run the app and return the exit status code of the QApplication
    sys.exit(app.exec_())
