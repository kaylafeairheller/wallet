import logging

import flet as ft
from flet_core import FontWeight, padding
from keri.app import connecting
from keri.core import coring

from wallet.app.identifying.identifier import IdentifierBase

logger = logging.getLogger('wallet')


class CreateDefaultIdentifierPanel(IdentifierBase):
    """
    CreateDefaultIdentifierPanel class for creating a default identifier in the application.
    """

    def __init__(self, app):
        self.app = app
        self.org = connecting.Organizer(hby=app.agent.hby)
        self.alias = ft.TextField(
            label='Alias',
            hint_text='Local alias for identifier',
        )
        self.panel_ref = self.panel()

        super(CreateDefaultIdentifierPanel, self).__init__(app, self.panel_ref)

    async def createAid(self, _):
        if self.alias.value == '':
            await self.app.snack('Alias is required')
            return

        kwargs = dict(algo='salty')
        kwargs['salt'] = coring.Salter(raw=coring.randomNonce()[2:23].encode('utf-8')).qb64
        kwargs['icount'] = 1
        kwargs['isith'] = 1
        kwargs['ncount'] = 1
        kwargs['nsith'] = 1
        kwargs['toad'] = 0
        # TODO self.toad.value = str(self.recommendedThold(len(self.rotationList.controls)))
        kwargs['estOnly'] = False
        kwargs['DnD'] = False

        hab = self.app.hby.makeHab(name=self.alias.value, **kwargs)
        serder, _, _ = hab.getOwnEvent(sn=0)
        await self.app.snack(f'Created AID {hab.pre}.')

        self.reset()
        self.app.page.route = f'/workflows/identifiers/{hab.pre}/contacts/connect'
        await self.page.update_async()

    async def cancel(self, _):
        self.reset()
        self.app.page.route = '/home'
        await self.page.update_async()

    def reset(self):
        self.alias.value = ''

    def panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Create Default Identifier',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Row(
                        [
                            self.alias,
                        ]
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                'Create',
                                on_click=self.createAid,
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
