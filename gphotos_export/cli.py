import click, utils
#from gphotos_export import utils

@click.command()
@click.argument('path')
def main(path):
    print("Archives = %s" % path)
    utils.fullrun(path)

if __name__ == '__main__':
    main()