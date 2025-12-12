"""
Issuer module for the application.
"""

import logging

import flet as ft

logger = logging.getLogger('wallet')


class IssuerBase(ft.Column):
    """
    Base class for issuing workflows in the application.

    Args:
        app: The application object.
        panel: The panel object.
        title (ft.Row): The title panel.

    Attributes:
        app: The application object.
        panel: The panel object.
        card: The container for the panel.
    """

    def __init__(self, app, panel, title=None):
        self.app = app
        title = title if title else ft.Row()
        self.panel = panel
        self.card = ft.Container(
            content=self.panel,
            expand=True,
            alignment=ft.alignment.top_left,
        )

        super().__init__(
            [
                title,
                self.card,
            ],
            expand=True,
            scroll=ft.ScrollMode.ALWAYS,
        )

    @staticmethod
    def loadIssuers(agent):
        habs = agent.hby.habs.values()
        return [
            ft.dropdown.Option(
                key=hab.pre,
                text=f'{hab.name} | {hab.pre}',
                data=hab,
            )
            for hab in habs
        ]
    
    @staticmethod
    def loadContacts(org):
        contacts = org.list()
        contacts = sorted(contacts, key=lambda c: c['alias'])
        contacts = list(filter(lambda c: 'tag=witness' not in c['oobi'], contacts))
        return [
            ft.dropdown.Option(
                key=contact['id'],
                text=f'{contact['alias']} | {contact['id']}',
                data=contact,
            )
            for contact in contacts
        ]
    
    def loadRegistries():
        registries = ["nancy", "drew", "gary"]
        return [
            ft.dropdown.Option(
                key=r,
                text=f'{r}',
                data=r,
            )
            for r in registries
        ]
    
    def loadLECredentials():
        credentials = ["Bank of America", "GLEIF"]
        return [
            ft.dropdown.Option(
                key=c,
                text=f'{c}',
                data=c,
            )
            for c in credentials
        ]
