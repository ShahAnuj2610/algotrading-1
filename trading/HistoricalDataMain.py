import datetime

from trading.constants import CSV_PATH, BACK_TEST
from trading.data.DataManagerFactory import DataManagerFactory
from trading.zerodha.kite.Period import Period


def get_data(kite, candle_interval, period, instruments_helper, symbol, opening_time_list):
    """
    Downloads historical data for offline testing and saves it as CSV file in a specific directory
    :return:
    """
    path = CSV_PATH + "ohlc/"
    mode = BACK_TEST
    data_manager = DataManagerFactory(kite, mode).get_object(
        period=period,
        candle_interval=candle_interval,
        instruments_helper=instruments_helper
    )

    for opening_time in opening_time_list:
        start_time = opening_time.replace(hour=9, minute=15, second=0, microsecond=0)
        end_time = opening_time.replace(hour=15, minute=30, second=0, microsecond=0)
        file_name = path + symbol + "_" + str(start_time.date())

        data_manager.put_data_to_csv(file_name, symbol, start_time, end_time)

    data_manager.close()


def historical_data(kite, instruments_helper):
    start_time = datetime.datetime(2021, 11, 9, 9, 15, 0)
    opening_time_list = []

    for i in range(5):
        opening_time_list.append(start_time)
        start_time = start_time + datetime.timedelta(days=1)

    get_data(kite, 5, Period.MIN, instruments_helper, 'SBIN', opening_time_list)

