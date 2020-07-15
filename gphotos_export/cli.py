import click, utils
#from gphotos_export import utils

@click.command()
@click.argument('path')
@click.option('--albums/--no-albums', default=False)

def main(path,albums):
    options = {'albums': albums}
    utils.fullrun(path,options)

if __name__ == '__main__':
    main()