"""
This module contains custom widgets for this application.
"""
from urllib.error import URLError
from threading import Thread

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QComboBox, QPushButton, QMessageBox

from plot import plot_stocks

POSSIBLE_TIME_PERIODS = [
    '3d', '4d', '5d', '6d',
    '7d', '14d', '21d',
    '1M', '2M', '3M', '4M', '5M', '6M', '7M', '8M', '9M', '10M', '11M',
    '1Y', '2Y', '3Y', '4Y', '5Y', '6Y', '7Y'
]


class StockSelector(QHBoxLayout):
    """
    A grouping of widgets that allows the details of a stock to be input.
    """

    def __init__(self, stock_no, model):
        """
        Constructor for StockSelector.

        :param stock_no: The number of the stock this Selector should modify (1 or 2)
        :param model: The ConfigurationModel object to modify with changes.
        """
        super().__init__()

        # validate precondition that stock_no is 1 or 2
        if stock_no not in (1, 2):
            raise ValueError('stock_no must be 1 or 2')

        self.stock_no = stock_no
        self.model = model

        # Add a label with the stock number being altered
        label = QLabel('STOCK ' + str(stock_no))
        label.setStyleSheet('font-weight: bold')
        self.addWidget(label)

        # add a label for the input for the GF code
        code_label = QLabel('Google Finance Code:')
        self.addWidget(code_label)

        # create the input for GF code
        self.gf_code_input = QLineEdit()

        # load the existing value from the ConfigurationModel
        if stock_no == 1:
            code_text = model.stock_1_code
        else:
            code_text = model.stock_2_code

        self.gf_code_input.setText(code_text)

        # register handler for textChanged to update the saved model when the input is changed
        self.gf_code_input.textChanged.connect(self.code_changed)

        # add the GF code input widget
        self.addWidget(self.gf_code_input)

        # add a label for the input for the GF index
        index_label = QLabel('Google Finance Index:')
        self.addWidget(index_label)

        # create the input for GF index
        self.gf_index_input = QLineEdit()

        # load the existing value from the ConfigurationModel
        if stock_no == 1:
            index_text = model.stock_1_index
        else:
            index_text = model.stock_2_index
        self.gf_index_input.setText(index_text)

        # register handler for textChanged to update the saved model when the input is changed
        self.gf_index_input.textChanged.connect(self.index_changed)

        # add the GF index input widget
        self.addWidget(self.gf_index_input)

    def get_gf_code(self):
        """
        Getter for the GF code stored in the respective input box.

        :return: String - Google Finance stock code input to the LineEdit
        """
        return self.gf_code_input.text()

    def get_gf_index(self):
        """
        Getter for the GF index stored in the respective input box.

        :return: String - Google Finance stock Index input to the LineEdit
        """
        return self.gf_index_input.text()

    def code_changed(self, new_text):
        """
        Event handler for a change in the GF code input.

        :param new_text: The new text value of the input.
        :return: None
        """
        if self.stock_no == 1:
            self.model.stock_1_code = new_text
        else:
            self.model.stock_2_code = new_text

        self.model.save()  # persists the changes

    def index_changed(self, new_text):
        """
        Event handler for a change in the GF Index input.

        :param new_text: The new text value of the input.
        :return: None
        """
        if self.stock_no == 1:
            self.model.stock_1_index = new_text
        else:
            self.model.stock_2_index = new_text

        self.model.save()  # persists the changes


class TimePeriodsChooser(QHBoxLayout):
    """
    Abstraction for a number of widgets to choose Time Periods for graphs.
    """
    def __init__(self, n_time_periods, model):
        """
        Constructor for TimePeriodsChooser

        :param n_time_periods: The number of time periods to receive iinputs for.
        :param model: The ConfigurationModel to save the time periods to.
        """
        super().__init__()
        self.n_time_periods = n_time_periods
        self.model = model

        self.time_period_inputs = []  # list to hold reference to the QComboBox(es)

        for n in range(n_time_periods):
            layout = QVBoxLayout()

            # add label to distinguish which time period is being edited
            label = QLabel('Time Period {0}'.format(n + 1))
            layout.addWidget(label)

            # create the input QComboBox for the time period
            input_choice = QComboBox()

            # set editable to false so that user cannot type a new option in, they are fixed to the provided options
            input_choice.setEditable(False)

            # add all possible time period choices
            for tp in POSSIBLE_TIME_PERIODS:
                input_choice.addItem(tp)

            # perform a check to see if more time periods being chosen this time vs last time
            # if yes, load the first n where n is the size of the previous time_periods list
            if n < len(self.model.time_periods):
                selected_tp = self.model.time_periods[n]
                idx = POSSIBLE_TIME_PERIODS.index(selected_tp)

                if idx == -1:
                    idx = 0

                input_choice.setCurrentIndex(idx)
            else:
                input_choice.setCurrentIndex(0)  # else, just select the first option (so as there are no 'nothing selected') boxes

            # set up signal/slot handler for a new selection
            input_choice.currentIndexChanged.connect(self.handle_tps_changed)

            # add widget to the view
            layout.addWidget(input_choice)

            # add a reference to the input to the list
            self.time_period_inputs.append(input_choice)

            # add the vertical layout for this selector to the section
            self.addLayout(layout)

    def get_time_periods_list(self):
        """
        Utility method that iterates through each of the input boxes and builds a list of time periods to use.

        :return: List of time periods selected by the user.
        """
        tp_list = []

        for combobox in self.time_period_inputs:
            tp_list.append(combobox.currentText())

        return tp_list

    def handle_tps_changed(self, index):
        """
        Event handler for one of the input boxes' selection being changed.

        :param index: The new selected index. (not used)
        :return: None
        """

        # get the new list of time periods
        new_tp_list = self.get_time_periods_list()

        # update the model's time period list with the new list
        self.model.time_periods = new_tp_list

        # persist the model
        self.model.save()


class PlotStockButton(QPushButton):
    """
    Class for the Plot Stocks button, that invokes the graph rendering flow.
    """
    def __init__(self, graph_pane_collection, time_periods_chooser, stock_1_chooser, stock_2_chooser):
        """
        Constructor for PlotStockButton with references to key components which must be read from.

        :param graph_pane_collection: The GraphPaneCollection containing the output graphs to write to.
        :param time_periods_chooser: The TimePeriodChooser which contains the time period inputs for the graphs.
        :param stock_1_chooser: The StockSelector for stock 1 inputs
        :param stock_2_chooser: The StockSelector for stock 2 inputs
        """
        super().__init__("Plot Stocks")
        self.graph_pane_collection = graph_pane_collection
        self.time_periods_chooser = time_periods_chooser
        self.stock_1_chooser = stock_1_chooser
        self.stock_2_chooser = stock_2_chooser

        # connect the button's click signal to the custom event handler 'on_click'
        self.clicked.connect(self.on_click)

    def on_click(self):
        """
        Event handler for the button being clicked. Invokes rendering of new graphs. Handles errors with rendering
        as message box dialogs.

        :return: None
        """
        t = Thread(target=self.render_new, daemon=True)
        t.start()

    def render_new(self):
        # gather stock 1 details
        stock_1 = {
            'gf_code': self.stock_1_chooser.get_gf_code(),
            'gf_index': self.stock_1_chooser.get_gf_index()
        }

        # gather stock 2 details
        stock_2 = {
            'gf_code': self.stock_2_chooser.get_gf_code(),
            'gf_index': self.stock_2_chooser.get_gf_index()
        }

        # get time periods from TimePeriodChooser
        time_periods = self.time_periods_chooser.get_time_periods_list()

        # invoke the graph rendering
        try:
            success = plot_stocks(self.graph_pane_collection, stock_1, stock_2, time_periods)

            # handle erroneous inputs with a message box
            if not success:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)

                msg.setText("You have chosen invalid stocks.")
                msg.setWindowTitle("Invalid Stocks")
                msg.setStandardButtons(QMessageBox.Ok)

                msg.exec_()
        except URLError as error:
            # no connection, display error message
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Network Error")
            msg.setText("A network error occurred. Please ensure you are connected to the internet.")
            msg.setInformativeText(str(error))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
