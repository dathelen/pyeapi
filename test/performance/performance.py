import re
import os
import pprint as pp
import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.abspath(os.path.dirname(__file__))
OPTIMIZE = os.path.join(HERE, 'stopwatch-optimize_get')
DEV = os.path.join(HERE, 'stopwatch-develop')
ENTRY_RE = re.compile(r'\S\'\w+.(\w+).test_(\w+)\'\n\w+\nF(\d+.\d+)', re.M)


def open_report(dest):
    with open(dest) as f:
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


def extract_data(entries):
    y_vals = list()
    x_vals = list()
    for test in entries:
        y_vals.append(test['time'])
        x_vals.append(test['test_name'])

    return x_vals, y_vals

def plot_data(api, base_tests, new_tests):
    N = len(base_tests)

    y_vals = list()
    x_vals = list()

    sorted_base_tests = sorted(base_tests, key=lambda k: k['test_name'])
    sorted_new_tests = sorted(new_tests, key=lambda k: k['test_name'])

    base_x, base_y = extract_data(sorted_base_tests)
    new_x, new_y = extract_data(sorted_new_tests)

    ind = np.arange(N)  # the x locations for the groups
    width = 0.35       # the width of the bars

    fig, ax = plt.subplots()
    plt.gcf().subplots_adjust(bottom=0.65, left=0.20)
    rects1 = ax.bar(ind, base_y, width, color='r')
    rects2 = ax.bar(ind + width, new_y, width, color='y')

    # add some text for labels, title and axes ticks
    ax.set_ylabel('Time [sec]')
    ax.set_title(api)
    ax.set_xticks(ind + width)
    ax.set_xticklabels(base_x, rotation=45, rotation_mode="anchor", ha='right')

    # ax.legend((rects1[0], rects2[0]), ('Men', 'Women'))

    print 'Saving %s report' % api
    plt.savefig(os.path.join(HERE, api))


def main():
    base_values = parse_report(open_report(DEV))
    opt_values = parse_report(open_report(OPTIMIZE))
    # pp.pprint(values)
    for api, base in base_values.iteritems():
        compare = opt_values.get(api)
        plot_data(api, base, compare)

if __name__ == '__main__':
    main()
