from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site

from allauth.socialaccount.models import SocialApp
from allauth.socialaccount import providers

from backend.settings import SITE_ID


class Command(BaseCommand):
    help = 'Adds a social app key to the site, does not support m2m sites'

    def add_arguments(self, parser):
        # as_choices() provides a tuple (id, display_name) for each provider
        choices = [x[0] for x in providers.registry.as_choices()]
        parser.add_argument('provider', choices=choices)
        parser.add_argument('client_id')
        parser.add_argument('secret')
        parser.add_argument('--key')
        parser.add_argument('--name')
        parser.add_argument('--site', default=SITE_ID, type=int)

    def handle(self, *args, **options):
        provider = options['provider']
        client_id = options['client_id']
        secret = options['secret']

        if options['key'] is not None:
            key = options['key']
        else:
            key = ''

        if options['name'] is not None:
            name = options['name']
        else:
            name = provider

        if SocialApp.objects.filter(name=name).exists():
            raise CommandError("SocialApp with this name already exists")

        site = Site.objects.get(id=options['site'])

        app = SocialApp(name=name, provider=provider, client_id=client_id, secret=secret, key=key)
        app.save()
        app.sites.set([site])
        app.save()
