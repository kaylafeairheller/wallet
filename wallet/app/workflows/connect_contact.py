import logging

import flet as ft
from flet_core import FontWeight

from wallet.app.contacting.contact import ContactBase

logger = logging.getLogger('wallet')


class ConnectWithContactPanel(ContactBase):
    """
    ConnectWithContactPanel class for creating a contact and connecting it to the given AID.
    """
        
    def __init__(self, app, hab):
        self.app = app
        self.hab = hab

        self.alias = ft.TextField(label='Alias')
        self.oobi = ft.TextField(label='OOBI', width=400)

        super(ConnectWithContactPanel, self).__init__(app=app, panel=self.panel())

    async def connect(self, _):
        if self.alias.value == '':
            await self.app.snack('Alias is required')
            return

        await self.app.snack(f'Connecting contact {self.alias.value}...')

        self.app.page.route = f'/workflows/identifiers/{self.hab.pre}/contacts/{self.oobi}/multisig/create'
        await self.page.update_async()

    async def cancel(self, _):
        self.app.page.route = '/home'
        await self.page.update_async()

    def panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Connect With Someone',
                        weight=FontWeight.BOLD,
                        size=24
                    ),
                    ft.Text(
                        'Create Contact',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Row(
                        [
                            self.alias,
                        ]
                    ),
                    ft.Row(
                        [
                            self.oobi,
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Identifier',
                                        weight=FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        f'{self.hab.name} | {self.hab.pre}',
                                    ),
                                ]
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                'Connect',
                                on_click=self.connect,
                            ),
                            ft.ElevatedButton(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),]),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=ft.padding.only(left=10, top=15),
        )
