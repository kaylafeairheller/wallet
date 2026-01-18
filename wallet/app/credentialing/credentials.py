"""
Credentials module for the Wallet application.
"""

import logging

import flet as ft
from keri.app import grouping, habbing
from keri.core import coring, eventing, serdering
from keri.help import helping

from wallet.app import colouring
from wallet.app.credentialing.credential import CredentialBase
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class Credentials(CredentialBase):
    """
    Class representing credentials in the application.

    Attributes:
        page (ft.Page): The page object associated with the app.
        list (ft.Column): The column object representing the list of credentials.
    """

    def __init__(self, app):
        self.app = app
        self._page: ft.Page = app.page  # Store page reference (page property is read-only in Flet controls)
        self.list = ft.Column([], spacing=0, expand=True)

        super().__init__(app, ft.Container(content=self.list, padding=ft.Padding.only(bottom=125)))

    @property
    def page(self):
        return self._page

    def did_mount(self):
        self.page.run_task(self.refresh_credentials)

    async def refresh_credentials(self):
        """
        Refreshes the credentials by setting them to the current list.
        """
        await self.set_credentials()
        self.update()

    @log_errors
    async def set_credentials(self):
        """
        Sets the credentials for the list view.
        """
        self.list.controls.clear()
        has_credentials = False

        # Sort habs alphabetically by name
        sorted_habs = sorted(self.app.agent.hby.habs.values(), key=lambda h: h.name.lower())

        for hab in sorted_habs:
            saids = self.app.agent.rgy.reger.subjs.get(keys=hab.pre)
            # creds = self.app.agent.rgy.reger.cloneCreds(saids, hab.db)

            for s in saids:
                has_credentials = True
                tip = 'Credential'
                icon = ft.Icons.LOCK_OUTLINED

                logger.debug(f'Processing credential SAID: {s.qb64}')

                # saids = self.app.agent.rgy.reger.issus.get(keys=hab.pre)
                # scads = self.app.agent.rgy.reger.schms.get(keys=self.schema)
                # saids = [saider for saider in saids if saider.qb64 in [saider.qb64 for saider in scads]]

                # for said in saids:
                #     print(said)

                # Get the credential object for this said
                creder = self.app.agent.rgy.reger.creds.get(keys=(s.qb64,))

                view = ft.PopupMenuItem(content=ft.Text('View'), icon=ft.Icons.PAGEVIEW, on_click=self.view_credential)
                view.data = {'hab': hab, 'said': s.qb64, 'creder': creder}
                revoke = ft.PopupMenuItem(
                    content=ft.Text('Revoke'),
                    icon=ft.Icons.BLOCK,
                    on_click=self.revoke_credential,
                )
                revoke.data = {'hab': hab, 'said': s.qb64, 'creder': creder}

                title_row = ft.Row(
                    [
                        ft.Text(
                            hab.pre,
                            font_family='monospace',
                        ),
                    ]
                )
                tile = ft.ListTile(
                    leading=ft.Icon(
                        icon,
                        tooltip=tip,
                    ),
                    title=ft.Text(
                        value=hab.name,
                        color=colouring.Colouring.get(colouring.Colouring.ON_SURFACE),
                    ),
                    subtitle=title_row,
                    trailing=ft.PopupMenuButton(
                        tooltip=None,
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            view,
                            revoke,
                        ],
                    ),
                    on_click=self.view_credential,
                    data=hab,
                    shape=ft.StadiumBorder(),
                )
                self.list.controls.append(
                    ft.Container(
                        content=tile,
                    )
                )
                self.list.controls.append(ft.Divider(opacity=0.1))

        if not has_credentials:
            self.list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.LOCK_OPEN_OUTLINED, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text('No credentials yet', size=18, weight=ft.FontWeight.W_500),
                            ft.Text(
                                'Credentials you issue or receive will appear here',
                                size=14,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=ft.Padding.all(40),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            )

        self.update()

    async def view_credential(self, e):
        """
        View the credential details.

        Args:
            e: The event object containing the identifier data.

        Returns:
            None
        """
        data = e.control.data
        if isinstance(data, dict):
            hab = data['hab']
        else:
            hab = data
        await self.app.page.push_route(f'/credentials/{hab.pre}/view')

    @log_errors
    async def revoke_credential(self, e):
        """
        Revoke a credential using TEL revocation events.

        This is the KERI BADA-RUN approach to nullifying a credential.
        Creates a revocation event in the TEL and anchors it to the KEL.

        Args:
            e: The event object containing the credential data.

        Returns:
            None
        """
        data = e.control.data
        said = data['said']
        creder = data['creder']

        if not creder:
            await self.app.snack('Credential data not found')
            return

        # Show confirmation dialog
        async def close_dialog(e):
            self.app.page.pop_dialog()

        async def confirm_revoke(e):
            self.app.page.pop_dialog()
            await self._perform_revocation(creder)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('Revoke Credential'),
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_400, size=48),
                    ft.Text('Are you sure you want to revoke this credential?'),
                    ft.Text(''),
                    ft.Text(f'SAID: {said[:20]}...', font_family='monospace'),
                    ft.Text(''),
                    ft.Text('This action cannot be undone.', weight=ft.FontWeight.BOLD),
                ],
                tight=True,
            ),
            actions=[
                ft.OutlinedButton('Cancel', on_click=close_dialog),
                ft.Button('Revoke', on_click=confirm_revoke, style=ft.ButtonStyle(color=ft.Colors.RED_400)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app.page.show_dialog(dialog)

    @log_errors
    async def _perform_revocation(self, creder):
        """
        Perform the actual credential revocation.

        Args:
            creder: The credential to revoke.
        """
        try:
            # Find the registry for this credential
            regk = creder.status  # Registry key is in the status field
            registry = None
            for reg in self.app.agent.rgy.regs.values():
                if reg.regk == regk:
                    registry = reg
                    break

            if registry is None:
                await self.app.snack('Registry not found for credential')
                return

            hab = registry.hab

            # Create revocation event with timestamp
            dt = helping.nowIso8601()
            rserder = registry.revoke(said=creder.said, dt=dt)

            # Create seal linking registry event to issuer's KEL
            vcid = rserder.ked['i']
            rseq = coring.Seqner(snh=rserder.ked['s'])
            rseal = eventing.SealEvent(vcid, rseq.snh, rserder.said)
            rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

            # Anchor to KEL via interaction or rotation event
            if registry.estOnly:
                anc = hab.rotate(data=[rseal])
            else:
                anc = hab.interact(data=[rseal])

            aserder = serdering.SerderKERI(raw=anc)

            # Process revocation through registrar
            self.app.agent.registrar.revoke(creder, rserder, aserder)

            # Handle multisig coordination if GroupHab
            if isinstance(hab, habbing.GroupHab):
                smids = hab.db.signingMembers(pre=hab.pre)
                smids.remove(hab.mhab.pre)

                for recp in smids:
                    exn, atc = grouping.multisigRevokeExn(ghab=hab, said=creder.said, rev=rserder.raw, anc=anc)
                    self.app.agent.postman.send(src=hab.mhab.pre, dest=recp, topic='multisig', serder=exn, attachment=atc)

                await self.app.snack('Revocation request sent. Waiting for other participants...')
            else:
                await self.app.snack('Credential revoked successfully!')

            # Refresh the credentials list
            await self.refresh_credentials()

        except Exception as ex:
            logger.exception('Error revoking credential')
            await self.app.snack(f'Error revoking credential: {str(ex)}')
