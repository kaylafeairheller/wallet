import logging

import flet as ft
from flet_core import FontWeight, padding
from keri.app import connecting, grouping
from keri.app.habbing import GroupHab
from keri.core import coring, serdering, signing
from keri.core.eventing import SealEvent
from wallet.logs import log_errors
from wallet.app.identifying.identifier import IdentifierBase

logger = logging.getLogger('wallet')
import pprint


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
            ft.dropdown.Option(
                key=hab.name,
                text=f'{hab.name} | {hab.pre}' if hab.name else f'{hab.pre}',
                data=hab,
            )
            for hab in app.agent.hby.habs.values()
        ]
    
    @log_errors
    async def generate_nonce(self, _):
        print("GENERATING")
        # self.app.agent.rgy.loadRegistries()
        print(self.app.agent.rgy.regs)
        rgy = next(iter(self.app.agent.rgy.regs.values()))  # get one Registry object
        print(dir(rgy))
        pprint.pprint(rgy.__dict__)

        for r, v in self.app.agent.rgy.regs.items():
            print("REG", r)
            pprint.pprint(r)
            pprint.pprint(v.__dict__)
            pprint.pprint(v.hab.__dict__)
        return
    
    @log_errors
    async def create(self, _):
        await self.app.snack(f'Creating registry...')

        hab = self.app.agent.hby.habByName(self.alias.value)
        if hab is None:
            raise ValueError(f"{self.alias.value} is not a valid AID alias")
        
        self.nonce = signing.Salter().qb64
        # estOnly = "estOnly" in kwa and kwa["estOnly"]
        registry = self.app.agent.rgy.makeRegistry(name=self.registryName.value, prefix=hab.pre, nonce=self.nonce)

        rseal = SealEvent(registry.regk, "0", registry.regd)
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
                usage = input(f"Please enter a description of the credential registry: ")

            smids = hab.db.signingMembers(pre=hab.pre)
            smids.remove(hab.mhab.pre)

            for recp in smids:  # this goes to other participants only as a signaling mechanism
                exn, atc = grouping.multisigRegistryInceptExn(ghab=hab, vcp=registry.vcp.raw, anc=anc, usage=usage)
                self.app.agent.postman.send(src=hab.mhab.pre,
                                  dest=recp,
                                  topic="multisig",
                                  serder=exn,
                                  attachment=atc)

        # while not self.registrar.complete(pre=registry.regk, sn=0):
        #     self.rgy.processEscrows()
        #     yield self.tock

        print("Registry:  {}({}) \n\tcreated for Identifier Prefix:  {}".format(self.registryName.value,
                                                                                registry.regk, hab.pre))

        self.app.page.route = f'/home'
        await self.page.update_async()

    async def cancel(self, _):
        self.app.page.route = '/home'
        await self.page.update_async()

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
                    ft.Text(
                        'Local Identifier',
                        weight=FontWeight.BOLD,
                        size=18
                    ),
                    self.name,
                    ft.Text(
                        'Alias',
                        weight=FontWeight.BOLD,
                        size=18
                    ),
                    self.alias,
                    ft.Row(
                        [
                            ft.Text(
                                'Generate Nonce',
                                weight=FontWeight.BOLD,
                                size=18
                            ),
                            ft.ElevatedButton(
                                'Generate',
                                on_click=self.generate_nonce,
                            ),
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
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=padding.only(bottom=105),
        )
    
