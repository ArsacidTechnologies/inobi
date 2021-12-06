
from optparse import OptionParser
from inobi import run_prerun_hooks


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-m', '--migrations',
                      dest='migrations',
                      help='run migration hooks',
                      default=False,
                      action='store_true',
                      )
    opts, args = parser.parse_args()
    run_prerun_hooks(migrations=opts.migrations)
