import logging

import flet as ft
from flet_core import FontWeight, padding
from keri.app import connecting
from keri.core import coring

from wallet.app.identifying.identifier import IdentifierBase

logger = logging.getLogger('wallet')


class CreateIssueECRAuthPanel(IdentifierBase):
    """
    CreateIssueECRAuthPanel class for issuing ECR Auth.
    """

    def __init__(self, app):
        self.app = app
        self.org = connecting.Organizer(hby=app.agent.hby)
        self.panel_ref = self.panel()

        super(CreateIssueECRAuthPanel, self).__init__(app, self.panel_ref)

    def panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Issue ECR Auth',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Text(
                        'Coming soon!',
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                'Issue',
                                on_click=self.issue,
                            ),
                            ft.ElevatedButton(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=padding.only(bottom=105),
        )
    
    async def issue(self, _):
        await self.app.snack(f'Issuing ECR auth...')
        self.app.page.route = f'/home'
        await self.page.update_async()

    async def cancel(self, _):
        self.app.page.route = '/home'
        await self.page.update_async()
