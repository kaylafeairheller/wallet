import logging

import flet as ft
from flet_core import FontWeight, padding
from keri.app import connecting
from keri.core import coring

from wallet.app.identifying.identifier import IdentifierBase

logger = logging.getLogger('wallet')


class CreateMultiSigIdentifierPanel(IdentifierBase):
    """
    CreateMultiSigIdentifierPanel class for creating an identifier to use in the Group Multisig workflow.
    """

    def __init__(self, app):
        self.app = app
        self.org = connecting.Organizer(hby=app.agent.hby)
    
        self.witnesses = ft.Column([], spacing=0, expand=True)
    
        # Loading default witnesses
        self.witnessList = self.loadWitnesses(app)

        self.witnesses.controls.clear()

        for wit in self.witnessList:
            self.witnesses.controls.append(
                ft.Text(wit['text']),
            )

        self.alias = ft.TextField(
            label='Alias',
            hint_text='Local alias for identifier',
        )
        self.panel_ref = self.panel()

        super(CreateMultiSigIdentifierPanel, self).__init__(app, self.panel_ref)

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
        kwargs['estOnly'] = False
        kwargs['DnD'] = False

        # Select witnesses and set threshold
        wit_thold = self.recommendedThold(len(self.witnessList))
        kwargs['toad'] = wit_thold
        kwargs['wits'] = []

        count = 0
        for wit in self.witnessList:
            if count >= wit_thold:
                break

            kwargs['wits'].append(wit['key'])
            count += 1

        hab = self.app.hby.makeHab(name=self.alias.value, **kwargs)
        serder, _, _ = hab.getOwnEvent(sn=0)
        await self.app.snack(f'Created AID {hab.pre}.')

        self.app.agent.witners.push(dict(serder=serder))
        await self.app.snack(f'Creating {hab.pre}, waiting for witness receipts...')

        self.reset()
        self.app.page.route = f'/workflows/multisig/identifiers/{hab.pre}/contacts/connect'
        await self.page.update_async()

    @staticmethod
    def loadWitnesses(app):
        return [
            {
                'key': wit['id'],
                'text': f'{wit["alias"]} | {wit["id"]}' if wit['alias'] else f'{wit["id"]}',
                'data': (wit['id'], wit['alias']),
            }
            for wit in app.witnesses
        ]

    @staticmethod
    def recommendedThold(numWits):
        match numWits:
            case 0:
                return 0
            case 1:
                return 1
            case 2 | 3:
                return 2
            case 4:
                return 3
            case 5 | 6:
                return 4
            case 7:
                return 5
            case 8 | 9:
                return 7
            case 10:
                return 8

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
                        'Create Identifier',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Text(
                        'This Identifier is for use in the Multisig Group.',
                    ),
                    ft.Row(
                        [
                            self.alias,
                        ]
                    ),
                    ft.Text(
                        'Witnesses Available:',
                        weight=FontWeight.BOLD,
                    ),
                    self.witnesses,
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
