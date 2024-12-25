from importlib import import_module
import click
import os


def register(app):
    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    @translate.command()
    def update():
        """Update all languages."""
        if os.system('pybabel extract -F app/babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system('pybabel update -i messages.pot -d app/translations'):
            raise RuntimeError('update command failed')
        os.remove('messages.pot')
        if os.system('chmod g+w -R app/translations'):
            raise RuntimeError('chmod command failed')


    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system('pybabel compile -f -d app/translations'):
            raise RuntimeError('compile command failed')

    @translate.command()
    @click.argument('lang')
    def init(lang):
        """Initialize a new language."""
        if os.system('pybabel extract -F app/babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system(
                'pybabel init -i messages.pot -d app/translations -l ' + lang):
            raise RuntimeError('init command failed')
        os.remove('messages.pot')
        if os.system('chmod g+w -R app/translations'):
            raise RuntimeError('chmod command failed')

    @app.shell_context_processor
    def make_shell_context():
        return {'User': 'bla'}
