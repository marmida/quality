'''
Things that generate reports from the results of a quality contest.
'''

import sys

def print_report(results):
    '''
    Print the results via stdout.

    todo: pass in the output stream as an argument, so it can be overriden
    this would currently change the protocol for reporters
    '''
    # get a list of judge names from the first result item
    judge_names = results.itervalues().next()[0].scores.keys()

    chart = ['File', 'Item'] + judge_names + ['Final']
    for src_path, contestants in results.iteritems():
        for contestant in contestants:
            chart.append([src_path, contestant.name] + ordered_scores(contestant.scores, judge_names) + [contestant.final_score])

    write_minimal_columns(chart, sys.stdout)

def write_minimal_columns(chart, output):
    '''
    Write the data structure `chart` to the file-like object `output`.

    `chart` must be a two-dimensional iterable of values to be written.  The 
    outer iterable is assumed to represent rows, and the inner iterables, 
    columns.

    The iterables must allow for by-index access, i.e., it[0] must return
    the first element.

    Formats the `chart` in the following ways:
    * right-aligns numeric values (float, int, complex, and long)
    * left-aligns all other data types
    * formats floats at 3 decimals of precision, with rounding
    * puts two spaces between each column
    * sizes each column to contain just enough space for its contents

    todo: allow for configuration options, say, to change formatting, like
    decimal precision.
    '''
    if len(chart) == 0:
        return

    # implementation note: there follow a lot of 'for' loops around
    # comprehensions.  I intentionally did this over using nested comprehensions,
    # although the whole function stands to be reviewed for efficiency.

    # convert all values in chart to strings
    # todo: find a better way to do this that doesn't duplicate memory
    text_chart = []
    for row in chart:
        text_chart.append(['%.3f' % col if type(col) == float else str(col) for col in row])
    
    # find the longest cell in each column; make a list, indexed by column
    max_len = []
    for i in range(len(chart[0])):
        max_len.append(max(len(row[i]) for row in text_chart))

    # overwrite text_chart cell values with justified padding
    for i, row in enumerate(text_chart):
        for j, cell in enumerate(row):
            justifier = cell.rjust if type(chart[i][j]) in [int, float, complex, long] else cell.ljust
            text_chart[i][j] = justifier(max_len[j])

    for row in text_chart:
        output.write('  '.join(row) + '\n')


def ordered_scores(scores, judge_names):
    '''
    Return a list of values in `scores`, ordered so their keys match
    their order of occurrence in `judge_names` 
    '''
    scores = scores.items()
    scores.sort(key=lambda i: judge_names.index(i[0]))
    return [i[1] for i in scores]