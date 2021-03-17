import matplotlib.pyplot as plt
import pandas as pd
import sys


def plotRenko(filename):
    # Turn interactive mode off
    plt.ioff()
    df = pd.read_csv(filename)

    # number of bars to display in the plot
    num_bars = 50

    # get the last num_bars
    df = df.tail(num_bars)
    renkos = zip(df['Open'], df['Close'])

    # compute the price movement in the Renko
    price_move = abs(df.iloc[1]['Open'] - df.iloc[1]['Close'])

    # create the figure
    fig = plt.figure(1)
    fig.clf()
    axes = fig.gca()

    # plot the bars, blue for 'up', red for 'down'
    index = 1
    for open_price, close_price in renkos:
        if open_price < close_price:
            renko = plt.Rectangle((index, open_price), 1, close_price - open_price, edgecolor='darkblue',
                                                 facecolor='blue', alpha=0.5)
            axes.add_patch(renko)
        else:
            renko = plt.Rectangle((index, open_price), 1, close_price - open_price, edgecolor='darkred',
                                                 facecolor='red', alpha=0.5)
            axes.add_patch(renko)
        index = index + 1

    # adjust the axes
    plt.xlim([0, num_bars])
    plt.ylim([min(min(df['Open']), min(df['Close'])), max(max(df['Open']), max(df['Close']))])
    fig.suptitle(
        'Bars from ' + min(df['Time']) + " to " + max(df['Time']) + '\nPrice movement = ' + str(price_move), fontsize=14)
    plt.xlabel('Bar Number')
    plt.ylabel('Price')
    plt.grid(True)
    plt.show()

    # save the figure as a png file
    fig.savefig("Renko.png")


if __name__ == "__main__":
    plotRenko("ashok.csv")