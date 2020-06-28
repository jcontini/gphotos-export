import click, utils
#from gphotos_export import utils

@click.command()
@click.argument('path')
def main(path):
    print("Path = %s" % path)
    utils.enumerate_zips(path)

if __name__ == '__main__':
    main()