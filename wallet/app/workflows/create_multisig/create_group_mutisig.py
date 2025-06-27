import logging

import flet as ft
from flet_core import FontWeight

from wallet.app.identifying.identifier import IdentifierBase

logger = logging.getLogger('wallet')


class CreateMutisigPanel(IdentifierBase):
    """
    CreateMutisigPanel class for creating a Group Multisig with two given identifiers.
    """
        
    def __init__(self, app, hab, oobi):
        self.app = app
        self.hab = hab
        self.oobi = oobi

        self.order = ["yours", "theirs"]  # Default order
        self.lead = ft.Column()
        self.recipient = ft.Column() 

        super().__init__(app=app, panel=self.panel())
        self.refresh_fields()

    async def create(self, _):
        await self.app.snack(f'Creating Group Multisig...')
        self.app.page.route = f'/home'
        await self.page.update_async()

    async def cancel(self, _):
        self.app.page.route = '/home'
        await self.page.update_async()

    def refresh_fields(self):
        """Update the field layout based on current order."""
        self.lead.controls.clear()
        self.lead.controls.append(self.get_column(self.order[0]))
        self.recipient.controls.clear()
        self.recipient.controls.append(self.get_column(self.order[1]))

    def get_column(self, label):
        if label == "yours":
            return ft.Row(
                    [
                        ft.Text('Your Identifier', weight=FontWeight.BOLD),
                        ft.Text(f'{self.hab.name} | {self.hab.pre}'),
                    ]
                )
        elif label == "theirs":
            return ft.Row(
                    [
                        ft.Text('Connecting Identifier', weight=FontWeight.BOLD),
                        ft.Text(self.oobi),
                    ]
                )

    def swap_order(self, _):
        """Swap identifier order."""
        self.order.reverse()
        self.refresh_fields()
        self.page.update()

    def panel(self):
        self.fields_column = ft.Column()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Create Group Multisig',
                        weight=FontWeight.BOLD,
                        size=24
                    ),
                    ft.Text(
                        'Lead',
                        weight=FontWeight.BOLD,
                        size=18
                    ),
                    self.lead,
                    ft.Text(
                        'Recipient',
                        weight=FontWeight.BOLD,
                        size=18
                    ),
                    self.recipient,
                    ft.Row(
                        [
                            ft.TextButton("Swap Order", on_click=self.swap_order),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                'Create',
                                on_click=self.create,
                            ),
                            ft.ElevatedButton(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ]
            ),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=ft.padding.only(left=10, top=15),
        )
