from datetime import datetime

from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from delay_analysis.delay_forcaster import DataForcaster


class DisplayDelay:
    metro_tram_data = {'dframe': pd.DataFrame(), 'time': [], 'delay': [], 'ticks': 1000}
    bus_data = {'dframe': pd.DataFrame(), 'time': [], 'delay': [], 'ticks': 1800}
    # containing the whole data
    dframe = {'dframe': pd.DataFrame(), 'time': [], 'delay': [], 'ticks': 1800}

    def __init__(self, delay_files):
        self.delay_files = delay_files

    def parse_file(self):
        data = []
        header = []
        i = 0
        for data_file in self.delay_files:
            file = open(data_file, 'r')
            while True:
                line = file.readline()
                if not line: break
                attributes = line.split(',', maxsplit=4)
                attributes = [attribute.strip().replace('\n', '') for attribute in attributes]
                if i == 0:
                    header = attributes
                    i = i + 1
                    continue
                delays = (attributes[4:][0].replace('[', '').replace(']', '')).split(',')
                try:
                    delays = [int(delay.replace(' ', '')) for delay in delays]
                    mean = np.array(delays).mean() * 0.001  # ms to s
                    sub_data = [int(attributes[0]),
                                datetime.strptime(attributes[1], "%d/%m/%Y %H:%M:%S"),
                                int(attributes[2]), int(attributes[3]), ]
                    sub_data = np.append(sub_data, mean)
                    data.append(sub_data)
                except ValueError:
                    # The ERROR attribute
                    continue
        self.dframe['dframe'] = pd.DataFrame(data, columns=header, )

    def simplify_data(self):
        dframe = self.dframe['dframe']
        self.__set_vehicle_data(dframe)

        self.metro_tram_data = self.__set_data(self.metro_tram_data)
        self.bus_data = self.__set_data(self.bus_data, )
        self.dframe = self.__set_data(self.dframe, )

    def plot_data(self):
        fig, axes = plt.subplots(3)
        self.__plot_subdata(self.metro_tram_data, axes[0], title='Metro and Tram Data', color_map='limegreen')
        self.__plot_subdata(self.bus_data, axes[1], title='Bus Data', color_map='darkviolet')
        self.__plot_subdata(self.dframe, axes[2], title='Whole Data', color_map='violet')
        fig.tight_layout()
        plt.show()

    @staticmethod
    def __plot_subdata(data, axes, title='', color_map='orange'):
        # limiting the number of ticks
        axes.plot(data['time'], data['delay'], linewidth=1, color=color_map)
        axes.set_xlabel('Date')
        axes.set_ylabel('Delay(s)')
        axes.set_title(title)
        axes.set_xticks((data['dframe'].index.tolist())[::data['ticks']], minor=False)
        axes.grid()

    def plot_data_decomposition(self):
        self.plot_subdata_decomposition(data_obj=self.dframe)
        plt.show()

    @staticmethod
    def plot_subdata_decomposition(data_obj):
        data = data_obj['dframe']['delays']
        result = seasonal_decompose(x=data, model='additive', period=180)
        figure = result.plot(resid=False)
        for axe in figure.axes:
            axe.set_xticks(data.index[::data_obj['ticks']], minor=False)
            axe.grid()

    def __set_vehicle_data(self, dframe: pd.DataFrame):
        metro_tram_condition = dframe['line_id'] <= 7
        bus_condition = dframe['line_id'] > 7
        # metro data
        data_frame = self.__arrange_data(dframe[metro_tram_condition])
        self.metro_tram_data['dframe'] = pd.concat([self.metro_tram_data['dframe'], data_frame])
        # tram data
        # bus data data
        data_frame = self.__arrange_data(dframe.loc[bus_condition])
        self.bus_data['dframe'] = pd.concat([self.bus_data['dframe'], data_frame])

    @staticmethod
    def __arrange_data(dframe):
        dframe = dframe.groupby(['date']).mean()
        dframe = dframe.sort_index()
        return dframe

    @staticmethod
    def __set_data(obj, remove_outlier=True):
        if remove_outlier:
            obj['dframe'] = obj['dframe'][obj['dframe']['delays'] <= 10000]
        dframe = obj['dframe'].groupby(['date']).mean().sort_index()
        obj['dframe'] = dframe
        obj['time'] = np.array(dframe.index.tolist())
        obj['delay'] = dframe['delays'].tolist()
        return obj

    def start_forcasting(self):
        forcaster = DataForcaster(self.dframe['dframe'])
        forcaster.set_data_shape()
        # forcaster.plot()
        # forcaster.define_params()
        forcaster.perform_training()
