import logging

import flet as ft
from flet import FontWeight, Padding
from keri.app import connecting, grouping
from keri.app.habbing import GroupHab
from keri.core import serdering, signing
from keri.core.eventing import SealEvent

from wallet.app.identifying.identifier import IdentifierBase
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class CreateRegistryPanel(IdentifierBase):
    """
    CreateRegistryPanel class for creating a registry.
    """

    def __init__(self, app):
        self.app = app
        self.org = connecting.Organizer(hby=app.agent.hby)

        self.alias = ft.Dropdown(
            options=self.loadIdentifiers(app),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
        )
        self.registryName = ft.TextField(
            label='Registry Name',
            hint_text='Name for new Registry',
        )
        self.usage = ft.TextField(
            label='Registry Description',
            hint_text='Describe how the Registry will be used.',
        )

        self.name = ft.Dropdown(
            options=self.loadIdentifiers(app),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
        )
        self.panel_ref = self.panel()
        super(CreateRegistryPanel, self).__init__(app, self.panel_ref)

    @staticmethod
    def loadIdentifiers(app):
        return [
            ft.DropdownOption(
                key=hab.name,
                text=f'{hab.name} | {hab.pre}' if hab.name else f'{hab.pre}',
                data=hab,
            )
            for hab in app.agent.hby.habs.values()
        ]

    @log_errors
    async def generate_nonce(self, _):
        """Debug function to inspect registries."""
        logger.debug('Inspecting registries...')
        logger.debug(f'Registries: {self.app.agent.rgy.regs}')
        if self.app.agent.rgy.regs:
            rgy = next(iter(self.app.agent.rgy.regs.values()))
            logger.debug(f'Registry attrs: {rgy.__dict__}')
        for r, v in self.app.agent.rgy.regs.items():
            logger.debug(f'Registry {r}: {v.__dict__}')
        return

    @log_errors
    async def create(self, _):
        await self.app.snack('Creating registry...')

        hab = self.app.agent.hby.habByName(self.alias.value)
        if hab is None:
            raise ValueError(f'{self.alias.value} is not a valid AID alias')

        self.nonce = signing.Salter().qb64
        # estOnly = "estOnly" in kwa and kwa["estOnly"]
        registry = self.app.agent.rgy.makeRegistry(name=self.registryName.value, prefix=hab.pre, nonce=self.nonce)

        rseal = SealEvent(registry.regk, '0', registry.regd)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)
        # if estOnly:
        #     anc = hab.rotate(data=[rseal])
        # else:
        anc = hab.interact(data=[rseal])

        aserder = serdering.SerderKERI(raw=bytes(anc))
        self.app.agent.registrar.incept(iserder=registry.vcp, anc=aserder)

        if isinstance(hab, GroupHab):
            usage = self.usage.value
            if usage is None:
                usage = input('Please enter a description of the credential registry: ')

            smids = hab.db.signingMembers(pre=hab.pre)
            smids.remove(hab.mhab.pre)

            for recp in smids:  # this goes to other participants only as a signaling mechanism
                exn, atc = grouping.multisigRegistryInceptExn(ghab=hab, vcp=registry.vcp.raw, anc=anc, usage=usage)
                self.app.agent.postman.send(src=hab.mhab.pre, dest=recp, topic='multisig', serder=exn, attachment=atc)

        # while not self.registrar.complete(pre=registry.regk, sn=0):
        #     self.rgy.processEscrows()
        #     yield self.tock

        logger.info(f'Registry {self.registryName.value} ({registry.regk}) created for {hab.pre}')

        await self.app.page.push_route('/home')

    async def cancel(self, _):
        await self.app.page.push_route('/home')

    def panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Create Registry',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Row(
                        [
                            self.registryName,
                            self.usage,
                        ]
                    ),
                    ft.Text('Local Identifier', weight=FontWeight.BOLD, size=18),
                    self.name,
                    ft.Text('Alias', weight=FontWeight.BOLD, size=18),
                    self.alias,
                    ft.Row(
                        [
                            ft.Text('Generate Nonce', weight=FontWeight.BOLD, size=18),
                            ft.Button(
                                'Generate',
                                on_click=self.generate_nonce,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Button(
                                'Create',
                                on_click=self.create,
                            ),
                            ft.Button(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            alignment=ft.Alignment.TOP_LEFT,
            padding=Padding.only(bottom=105),
        )
