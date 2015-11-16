import re
import os
import pprint as pp
import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.abspath(os.path.dirname(__file__))
PATH = os.path.join(HERE, 'stopwatch-optimize_get')
ENTRY_RE = re.compile(r'\S\'\w+.(\w+).test_(\w+)\'\n\w+\nF(\d+.\d+)', re.M)


def open_report():
    with open(PATH) as f:
        data = f.read()
        return data


def parse_report(data):
    entries = dict()
    matches = re.findall(ENTRY_RE, data)
    for entry in matches:
        api = entry[0]
        match = entries.get(api)
        if not match:
            entries[api] = list()

        test = dict(test_name=entry[1],
                    time=float(entry[2]))

        entries[api].append(test)

    return entries


def plot_data(api, tests):
    N = len(tests)

    y_vals = list()
    x_vals = list()
    sorted_tests = sorted(tests, key=lambda k: k['time'])

    for test in sorted_tests:
        y_vals.append(test['time'])
        x_vals.append(test['test_name'])

    # menStd = (2, 3, 4, 1, 2)

    ind = np.arange(N)  # the x locations for the groups
    width = 0.35       # the width of the bars

    fig, ax = plt.subplots()
    plt.gcf().subplots_adjust(bottom=0.65, left=0.20)
    rects1 = ax.bar(ind, y_vals, width, color='r')

    # add some text for labels, title and axes ticks
    ax.set_ylabel('Time [sec]')
    ax.set_title(api)
    ax.set_xticks(ind + width)
    ax.set_xticklabels(x_vals, rotation=45, rotation_mode="anchor", ha='right')

    # ax.legend((rects1[0], rects2[0]), ('Men', 'Women'))

    print 'Saving %s report' % api
    plt.savefig(os.path.join(HERE, api))


def main():
    values = parse_report(open_report())
    # pp.pprint(values)
    for api, tests in values.iteritems():
        plot_data(api, tests)

if __name__ == '__main__':
    main()
