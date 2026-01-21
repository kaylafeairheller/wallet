import asyncio
import logging

import flet as ft
from keri.app import grouping, habbing
from keri.core import coring, eventing, serdering, signing

from wallet.logs import log_errors
from wallet.notifying.notification import NotificationsBase

logger = logging.getLogger('wallet')


class NoticeCredentialIssuance(NotificationsBase):
    """
    Represents a notification for a credential issuance request in a multisig group.

    Args:
        app (App): The application instance.
        note (Note): The notification object.

    Attributes:
        app (App): The application instance.
        note (Note): The notification object.
        said (str): The notification attribute 'd'.
        ked (Optional[dict]): The cloned KERI event data.
        embeds (Optional[dict]): The embedded data containing acdc, iss, anc.
    """

    def __init__(self, app, note):
        self.app = app
        logger.debug('~~~ CREDENTIAL ISSUANCE NOTE ~~~~')
        logger.debug(f'NOTE: {note.__dict__}')
        logger.debug(f'ATTRS: {note.attrs}')
        self.note = note
        self.said = note.attrs['d']
        self.ked = None
        self.embeds = None
        self.creder = None
        self.iserder = None
        self.anc = None

        self.btn_approve = ft.Button(
            'Approve',
            on_click=self.approve,
            data=note.rid,
            disabled=True,
        )

        self.group_info_pacifier = ft.Row([ft.Text('Fetching credential information...')], visible=True)

        self.credential_said = ft.TextField(
            label='Credential SAID',
            value='',
            read_only=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )

        self.schema_said = ft.TextField(
            label='Schema',
            value='',
            read_only=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )

        self.issuer_id = ft.TextField(
            label='Issuer',
            value='',
            read_only=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )

        self.recipient_id = ft.TextField(
            label='Recipient',
            value='',
            read_only=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )

        self.attributes_list = ft.Column([])

        self.credential_info = ft.Column(
            controls=[
                self.credential_said,
                self.schema_said,
                self.issuer_id,
                self.recipient_id,
                ft.Divider(),
                ft.Row([ft.Text('Credential Attributes:')]),
                self.attributes_list,
            ],
            visible=False,
            width=500,
        )

        super().__init__(
            app,
            self.panel(),
            ft.Row(
                controls=[
                    ft.Container(
                        ft.Text(value='Credential Issuance Request', size=24),
                        padding=ft.Padding.only(left=10, top=0, right=10, bottom=0),
                    ),
                    ft.Container(
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=self.cancel),
                        alignment=ft.Alignment.TOP_RIGHT,
                        expand=True,
                        padding=ft.Padding.only(left=0, top=0, right=10, bottom=0),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    async def cancel(self, e):
        await self.app.page.push_route('/notifications')
        self.app.page.update()

    def did_mount(self):
        self.page.run_task(self.get_exchange_message)

    @log_errors
    async def get_exchange_message(self):
        """
        Retrieves the exchange message from the agent's cloner and updates the UI.
        """
        self.app.agent.cloner.clone(self.said)

        while self.said not in self.app.agent.cloner.cloned:
            await asyncio.sleep(1)

        cloned = self.app.agent.cloner.cloned[self.said]

        logger.debug(f'Cloned: {cloned.__dict__}')

        self.ked = cloned.ked
        self.embeds = cloned.embeds

        # Extract the ACDC (credential), issuance event, and anchor
        if 'acdc' in self.embeds:
            acdc_raw = self.embeds['acdc']
            self.creder = serdering.SerderACDC(raw=acdc_raw)

            self.credential_said.value = self.creder.said
            self.schema_said.value = self.creder.schema
            self.issuer_id.value = self.creder.issuer

            # Get recipient from subject
            if hasattr(self.creder, 'subject') and 'i' in self.creder.subject:
                self.recipient_id.value = self.creder.subject['i']

            # Display credential attributes
            attrib = self.creder.attrib if hasattr(self.creder, 'attrib') else {}
            for key, value in attrib.items():
                if key not in ['i', 'd']:  # Skip technical fields
                    self.attributes_list.controls.append(
                        ft.TextField(
                            label=key,
                            value=str(value),
                            read_only=True,
                            text_style=ft.TextStyle(font_family='monospace'),
                        )
                    )

        if 'iss' in self.embeds:
            self.iserder = serdering.SerderKERI(raw=self.embeds['iss'])

        if 'anc' in self.embeds:
            self.anc = self.embeds['anc']

        self.group_info_pacifier.visible = False
        self.credential_info.visible = True
        self.btn_approve.disabled = False

        self.update()

    def panel(self):
        """
        Creates and returns a panel containing the credential issuance request information.
        """
        return ft.Container(
            ft.Column(
                [
                    self.group_info_pacifier,
                    self.credential_info,
                    ft.Row(
                        [
                            self.btn_approve,
                            ft.Button('Dismiss', on_click=self.dismiss),
                        ]
                    ),
                    ft.Container(padding=ft.Padding.only(bottom=80)),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.Padding.only(left=10, top=15, bottom=100),
        )

    @log_errors
    async def approve(self, e):
        """
        Approve the credential issuance request by contributing to the multisig.
        """
        if not self.creder or not self.iserder:
            await self.app.snack('Credential data not loaded yet')
            return

        await self.app.snack('Approving credential issuance...')

        try:
            # Find the registry for this credential
            registry = None
            for reg in self.app.agent.rgy.regs.values():
                if reg.regk == self.iserder.pre:
                    registry = reg
                    break

            if registry is None:
                await self.app.snack('Registry not found')
                return

            hab = registry.hab

            if not isinstance(hab, habbing.GroupHab):
                await self.app.snack('Not a group identifier')
                return

            # Create seal linking registry event to issuer's KEL
            vcid = self.iserder.ked['i']
            rseq = coring.Seqner(snh=self.iserder.ked['s'])
            rseal = eventing.SealEvent(vcid, rseq.snh, self.iserder.said)
            rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

            # Anchor to KEL via interaction event
            anc = hab.interact(data=[rseal])
            aserder = serdering.SerderKERI(raw=anc)

            # Process issuance through credentialer and registrar
            self.app.agent.credentialer.issue(self.creder, self.iserder)
            self.app.agent.registrar.issue(self.creder, self.iserder, aserder)

            # Send approval to other group members
            smids = hab.db.signingMembers(pre=hab.pre)
            smids.remove(hab.mhab.pre)

            # Serialize ACDC with signing artifacts
            acdc = signing.serialize(
                self.creder,
                coring.Prefixer(qb64=self.iserder.pre),
                coring.Seqner(sn=self.iserder.sn),
                coring.Saider(qb64=self.iserder.said),
            )

            for recp in smids:
                exn, atc = grouping.multisigIssueExn(ghab=hab, acdc=acdc, iss=self.iserder.raw, anc=anc)
                self.app.agent.postman.send(src=hab.mhab.pre, dest=recp, topic='multisig', serder=exn, attachment=atc)

            await self.app.snack('Credential issuance approved!')
            await self.app.page.push_route('/credentials')
            self.app.page.update()

        except Exception as ex:
            logger.exception('Error approving credential issuance')
            await self.app.snack(f'Error: {str(ex)}')

    async def dismiss(self, _):
        """
        Dismisses the notification and updates the page route.
        """
        await self.app.page.push_route('/notifications')
        self.app.page.update()
