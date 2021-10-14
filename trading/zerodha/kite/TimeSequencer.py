import datetime

from trading.zerodha.kite.Period import Period


def get_time_sequence(period, candle_interval, candle_length, start_time):
    if start_time.hour > 15:
        raise ValueError(
            "Outside of market hours. Given hour {} and minute {}".format(start_time.hour, start_time.minute))
    elif start_time.hour == 15 and start_time.minute > 30:
        raise ValueError(
            "Outside of market hours. Given hour {} and minute {}".format(start_time.hour, start_time.minute))

    trading_holidays = [
        datetime.date(2021, 10, 15),
        datetime.date(2021, 11, 4),
        datetime.date(2021, 11, 5),
        datetime.date(2021, 11, 19)
    ]

    sequence = []
    start_time = start_time.replace(second=0)
    prev = start_time

    delta = get_time_delta(period, candle_interval)

    for i in range(candle_length):
        prev = prev.replace(second=0)
        prev = prev - delta

        if prev.hour == 9 and prev.minute <= 15:
            while True:
                prev = prev - datetime.timedelta(days=max(1, (prev.weekday() + 6) % 7 - 3))

                if prev.date() in trading_holidays:
                    continue

                break

            prev = prev.replace(hour=15)
            prev = prev.replace(minute=30)
            prev = prev - delta

        sequence.append(prev)

    return sequence


def get_time_delta(period, candle_interval):
    if period == Period.MIN:
        return datetime.timedelta(minutes=candle_interval)
    else:
        raise ValueError("Only minute iterations are supported")


def get_previous_time(period, candle_interval, start_time):
    return get_time_sequence(period, candle_interval, 1, start_time)[0]


def get_previous_trading_day():
    """
    Find the previous trading day by considering various parameters (viz. holidays, treading hours etc)
    :return: Previous trading day
    """
    now = datetime.datetime.now()

    if now.weekday() == 5 or now.weekday() == 6 or (now.weekday() == 0 and now.hour <= 15):
        # if its a saturday, sunday or monday (before market hours), then find the last active trading day
        # Reuses the get_time_sequence function which assumes it will not be called in the after market hours
        # Hence we mimic by mutating the current time
        now = now.replace(hour=9)
        now = now.replace(minute=10)
        prev_time = get_previous_time(Period.MIN, 1, now).date()
    else:
        # All the exceptional scenarios are covered above. The remaining situations mean either the market is
        # active or the market has ended today. Hence the last trading day has to be today
        prev_time = now.date()

    return prev_time


def get_missing_time(actual_time_list, expected_time_list):
    expected_time_list = [str(i) for i in expected_time_list]
    actual_time_list = [str(i) for i in actual_time_list]
    return list(set(expected_time_list) - set(actual_time_list))


'''
print(get_time_sequence(Period.MIN, 1, 7, datetime.datetime(year=2021,
                                                            month=9,
                                                            day=28,
                                                            hour=14,
                                                            minute=55,
                                                            second=59,
                                                            microsecond=0)))
'''
