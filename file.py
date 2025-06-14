import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


def main():
    data = [pd.read_json(file) for file in ['audio.json', 'video.json']]
    df = pd.concat(data, ignore_index=True)

    df['ts'] = pd.to_datetime(df['ts'])
    df = df.rename(columns={'ts': 'Date'})
    df = df.rename(columns={'ms_played': 'Time'})
    df['Date'] = df['Date'].dt.date
    df.sort_values('Date', inplace=True)

    highlight = []
    add_highlight(highlight, df['Date'].iloc[0], 'First day of data')
    add_highlight(highlight, '2024-02-01', 'Some random event')
    add_highlight(highlight, df['Date'].iloc[-1], "Last day of data")

    # pie_chart(df,'platform')
    # pie_chart(df,'shuffle')
    listen_chart(df, 2024, 'hours', highlight)
    # listen_chart(df, 2025, 'songs', highlight)



def add_highlight(list, date, label):
    return list.append((pd.Timestamp(date), label))


def listen_chart(df, year, choice, h):
    dates = None
    if choice == 'hours':
        dates = df.groupby('Date', as_index=False).sum()
        dates['Time'] /= (1000 * 60 * 60)  # ms to hour

    if choice == 'songs':
        dates = df[df['reason_end'].isin(['endplay', 'trackdone'])]
        dates = dates.groupby('Date', as_index=False).size().rename(columns={'size': 'Time'})

    d = fill_empty_dates(dates)
    y = year_df(d, year)
    fig, axes = plt.subplots(nrows=4,
                             ncols=3,
                             figsize=(20, 20),
                             dpi=500)

    highlight = [item for item in h if item[0].year == year]
    visualize(y, fig, axes, highlight, choice)


def pie_chart(df, name):
    chart = df[name] \
        .value_counts() \
        .reset_index()

    fig, ax = plt.subplots(layout='constrained')
    ax.set_title(f'{name} arányok')

    ax.pie(
        chart['count'],
        labels=chart[name],
        startangle=90,
        autopct='%1.1f%%'
    )
    plt.show()


def fill_empty_dates(df):
    start = df['Date'].min() - pd.offsets.YearBegin(1)  # the first appearing year's first day
    end = df['Date'].max() + pd.offsets.YearEnd(1)  # the last appearing year's last day
    r = pd.date_range(start, end)  # dataframe of dates ranging from first day to last day

    return (df.set_index('Date')  # fill all not existing values with -1 to distinguish from real values
            .reindex(r)  # (used so that each year is full 12 months and no empty plot space left)
            .fillna({'Time': -1})
            .reset_index()
            .rename(columns={'index': 'Date'}))


def year_df(df, year):
    return df[pd.to_datetime(df['Date']).dt.year == year]  # extract given year to a new dataframe
    # (used when choosing year in main() to plot)


def month_df(df, year, month):
    return df[(pd.to_datetime(df['Date']).dt.year == year)  # extract given year's given month to a new dataframe
              & (pd.to_datetime(df['Date']).dt.month == month)]  # (used when splitting a year into months to plot each month)


def df_calendar(date, time):
    i, j = [], []  # week number (i) and week day number (j)
    for d in date:  # given dataframe's date
        iso_year, week, weekday = d.isocalendar()  # extract year, week, weekday data from provided date
        if iso_year > d.year:  # mitigate so that no day will overflow to the next year, useful when there are 53 weeks
            week += 52
        i.append(week)  # fill week number (i)
        j.append(weekday - 1)  # fill week day number (j)
    i = np.array(i) - min(i)  # no idea what this does lmao
    calendar = np.nan * np.zeros((max(i) + 1, 7))  # fill a dataframe with empty values on its respective size (53x7 or 52x7)
    calendar[i, j] = time  # fill the dataframe with real values from Time's values

    return calendar, i, j  # this whole function is used so that dates and such can be plotted in labels


def label_days(ax, calendar, i, j, date):
    ni, nj = calendar.shape  # grep calendar's row num and column num
    day_of_month = np.nan * np.zeros((ni, nj))  # fill the dataframe with empty rows and columns
    day_of_month[i, j] = [d.day for d in date]  # fill the dataframe's rows and columns with real data

    for (i, j), day in np.ndenumerate(day_of_month):  # print numbering on the daily plots
        if np.isfinite(day):
            ax.text(j, i, int(day), ha='center', va='center', fontsize=12)

    ax.set_xticks(np.arange(nj))  # fill day's names
    ax.set_xticklabels(['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'], ha='center', fontsize=12)
    ax.xaxis.tick_top()


def label_months(ax, date, i):
    month_labels = np.array(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                             'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    months = np.array([d.month for d in date])  # store available month names from provided dataframe
    uniq_months = sorted(set(months))  # store month names uniquely, non-repetitively
    yticks = [np.median(i[months == m]) for m in uniq_months]  # places the month name in the middle of the axis? maybe.
    labels = [month_labels[m - 1] for m in uniq_months]  # no idea
    ax.set(yticks=yticks)
    ax.set_yticklabels(labels, rotation=90, fontsize=12)


def split_year(y):
    min_y = min(sorted(set(y['Date'].dt.month)))  # first day of the given month
    max_y = max(sorted(set(y['Date'].dt.month)))  # last day of the given month
    m = []
    for i in range(min_y, max_y + 1):  # put each month into a list, later to iterate through and plot one-by-one
        m_tmp = month_df(y, y['Date'].dt.year, i)
        m.append(m_tmp)
    return m


def visualize(df, fig, axes, highlight, choice):
    y_split = split_year(df)  # split given year's dataframe into months
    year = sorted(set(y_split[0]['Date'].dt.year))  # find the year's name (to output in the title)

    fig.subplots_adjust(top=0.95)  # reserve space for title

    if choice == 'hours':
        fig.suptitle(f'Daily listened hours ({year[0]})', fontsize=35, y=.99)  # print title, and the name of the year dynamically

    if choice == 'songs':
        fig.suptitle(f'Listened songs per day ({year[0]})', fontsize=35, y=.99)  # print title, and the name of the year dynamically

    fig.subplots_adjust(left=0.15)  # reserve space on the left side for the calculation table

    max_val = max(df['Time'].max() for df in y_split)  # maximum Step in the given year to set universal largest low-high range for bar

    plt.rcParams.update({  # set font that scale better to high DPI (500)
        'font.family': 'DejaVu Sans',
        'text.antialiased': True,
        'font.weight': 'normal'
    })

    # iterate through months
    i = 0
    for ax in axes.flat:

        # while i is smaller than the existing months (since we filled it, it's 12, but still, better this way)
        if i < len(y_split):
            calendar, week_num, day_num = df_calendar(y_split[i]['Date'], y_split[i][
                'Time'])  # extract date layout pre-filled (df_calendar) with data, week numbers, day numbers

            label_days(ax, calendar, week_num, day_num, y_split[i]['Date'])  # get the name of the 7 days of the week for the given week
            label_months(ax, y_split[i]['Date'], week_num)  # get the month's name

            cmap = plt.get_cmap('summer').copy()  # create a custom color map
            cmap.set_under('lightgray')  # mark under vmin values as lightgray, aka invalid (thus setting not existing dates as -1 in value)
            im = ax.imshow(calendar, interpolation='none', cmap=cmap, vmin=0,
                           vmax=max_val)  # set color map, min value, max value; no idea what is interpolation in this case (also note the set global maximum)

            cbar = fig.colorbar(im, ax=ax, shrink=0.8)  # set the color bar, shrink so looks more compact
            cbar.ax.tick_params(labelsize=12)  # color bar labels to be bit bigger

            # highlight dates
            if highlight:
                for target_date, note in highlight:  # Unpack tuple here
                    if (y_split[i]['Date'] == target_date).any():  # Now comparing Series vs single date
                        iso_year, target_week, target_weekday = target_date.isocalendar()
                        current_weeks = [d.isocalendar()[1] for d in y_split[i]['Date']]
                        min_week = min(current_weeks)
                        row = target_week - min_week
                        col = target_weekday - 1
                        rect = Rectangle(
                            (col - 0.5, row - 0.5),
                            1, 1,
                            edgecolor='red',
                            facecolor='none',
                            linewidth=1.5
                        )
                        ax.add_patch(rect)

                fig.subplots_adjust(left=.15, right=0.80)
                highlight_patches = [
                    Rectangle((0, 0), 1, 1, edgecolor='red', facecolor='none', linewidth=2)
                    for _ in highlight
                ]
                fig.legend(
                    handles=highlight_patches,
                    labels=[f"{d.strftime('%Y-%m-%d')}: {n}" for d, n in highlight],
                    loc='center right',
                    bbox_to_anchor=(.95, 0.5),
                    fontsize=10,
                    title='Highlighted dates',
                    title_fontsize='12'
                )

            i += 1  # don't forget to iterate the if statement

    plt.savefig('output.pdf', dpi=500)  # save the heatmap as pdf for best quality
    # plt.show()


main()
