from django.apps import AppConfig
from django.db.backends.signals import connection_created


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        def configure_sqlite(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                with connection.cursor() as cursor:
                    cursor.execute('PRAGMA journal_mode = WAL;')
                    cursor.execute('PRAGMA busy_timeout = 60000;')
                    cursor.execute('PRAGMA synchronous = NORMAL;')

        connection_created.connect(configure_sqlite)
