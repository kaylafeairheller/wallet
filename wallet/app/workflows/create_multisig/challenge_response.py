import asyncio
import logging

import flet as ft
import pyperclip
from flet import FontWeight
from keri.app.habbing import GroupHab
from keri.peer import exchanging
from mnemonic import mnemonic

from wallet.app.colouring import Colouring
from wallet.app.identifying.identifier import IdentifierBase

logger = logging.getLogger('wallet')


# TODO REMOVE
class MultisigChallengeResponsePanel(IdentifierBase):
    """
    MultisigChallengeResponsePanel class for handling challenge/response between contacts in the Create Group Multisig Workflow.
    """

    def __init__(self, app, hab, alias, aid):
        self.app = app
        self.hab = hab
        self.contact_alias = alias
        self.contact_aid = aid

        self.unverified = ft.Icon(
            ft.Icons.SHIELD_OUTLINED, size=32, color=Colouring.get(Colouring.RED), tooltip='Unverified', visible=True
        )
        self.verified = ft.Icon(ft.Icons.SHIELD_ROUNDED, size=32, tooltip='Verified', visible=True)

        self.phrase = ft.TextField(read_only=True, width=800)
        self.pacifier = ft.Text(italic=True, size=14, weight=ft.FontWeight.W_200)
        self.copy_phrase = ft.IconButton(icon=ft.Icons.COPY_ROUNDED, on_click=self.copy_challenge, visible=False)

        self.verify_challenge_text = ft.TextField(width=800, on_change=self.verify_enable)

        self.contact = f'{alias} | {aid}'

        super().__init__(app=app, panel=self.panel())

    async def accept(self, _):
        await self.app.snack('Accepting Challenge Response...')
        await self.app.page.push_route(
            f'/workflows/multisig/identifiers/{self.hab.pre}/contacts/{self.contact_alias}/{self.contact_aid}/multisig/create'
        )

    async def cancel(self, _):
        await self.app.page.push_route('/home')

    async def verify_enable(self, e):
        got_mnemonic = len(self.verify_challenge_text.value.split(' ')) == 12

        self.verify_button.disabled = False if got_mnemonic else True
        if got_mnemonic:
            self.verify_button.icon_color = ft.Colors.GREY_400
        self.update()

    async def verify_challenge(self, e):
        hab = self.app.hby.habs[self.selected_identifier]

        if self.identifiers.value is None:
            await self.app.snack('Select an identifier to verify with')
            self.app.page.update()
            return

        payload = dict(i=self.selected_identifier, words=self.verify_challenge_text.value.split(' '))

        exn, _ = exchanging.exchange(route='/challenge/response', payload=payload, sender=hab.pre)
        ims = hab.endorse(serder=exn, last=False, pipelined=False)
        del ims[: exn.size]

        senderHab = hab.mhab if isinstance(hab, GroupHab) else hab

        self.app.agent.postman.send(src=senderHab.pre, dest=self.contact['id'], topic='challenge', serder=exn, attachment=ims)

        while not self.app.agent.postman.cues:
            await asyncio.sleep(1.0)

        self.verify_challenge_text.value = ''
        self.app.page.update()
        await self.app.snack('Challenge response sent!')

    async def generate_challenge(self, e):
        del e
        mnem = mnemonic.Mnemonic(language='english')
        self.phrase.value = mnem.generate(strength=128)
        self.copy_phrase.data = self.phrase.value
        self.copy_phrase.visible = True
        self.update()

    async def copy_challenge(self, e):
        sig = self.contact['id']
        pyperclip.copy(e.control.data)

        await self.app.snack('Phrase Copied!')
        await asyncio.sleep(1.0)
        await self.app.snack('Waiting for challenge response')

        found = False
        i = 0
        while not found and not self.cancelled:
            self.pacifier.value = f'Waiting for challenge response{"." * i}'
            self.app.page.update()

            saiders = self.app.hby.db.reps.get(keys=(sig,))
            for saider in saiders:
                exn = self.app.hby.db.exns.get(keys=(saider.qb64,))

                if self.phrase.value == ' '.join(exn.ked['a']['words']):
                    found = True
                    self.app.hby.db.chas.add(keys=(sig,), val=saider)
                    break

            if found:
                break

            i += 1
            if i > 3:
                i = 0
            await asyncio.sleep(3)

        if found:
            self.pacifier.value = ''
            self.unverified.visible = False
            self.verified.visible = True
            self.update()

            await self.app.snack('Challenge successful.')
            self.app.page.update()

    def panel(self):
        self.verify_button = ft.IconButton(
            icon=ft.Icons.CHECK,
            on_click=self.verify_challenge,
            disabled=True,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text('Verify Contact', weight=FontWeight.BOLD, size=24),
                    ft.Text(self.contact, size=18),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text(f'Generate challenge to send to {self.contact_alias}', size=14),
                                        ft.IconButton(icon=ft.Icons.LOOP, on_click=self.generate_challenge),
                                    ]
                                ),
                                ft.Row([self.phrase, self.copy_phrase]),
                                ft.Row([self.pacifier]),
                            ]
                        )
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(f'Respond to a challenge {self.contact_alias} sent you', size=14),
                                ]
                            ),
                            ft.Row(
                                [
                                    self.verify_challenge_text,
                                    self.verify_button,
                                ]
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Button(
                                'Accept',
                                on_click=self.accept,
                            ),
                            ft.Button(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ]
            ),
            padding=ft.Padding.only(left=10, top=15),
        )
