"""
Abandon Identifier confirmation dialog.

This module provides a confirmation dialog for abandoning (nullifying) an identifier
following the KERI BADA-RUN philosophy (Best Available Data - Read, Update, Nullify).
"""

import logging

import flet as ft
from keri.app import grouping, habbing
from keri.core import serdering

from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class AbandonIdentifierDialog(ft.AlertDialog):
    """
    Confirmation dialog for abandoning an identifier.

    Abandoning an identifier rotates it to null keys (ncount=0, nsith='0'),
    making it permanently unusable. This is the proper KERI way to nullify
    an identifier rather than deleting it.
    """

    def __init__(self, app):
        self.app = app
        self.hab = None

        self.confirm_checkbox = ft.Checkbox(
            label='I understand this will rotate to NO NEXT KEYS',
            value=False,
            on_change=self.toggle_confirm_button,
        )

        self.btn_confirm = ft.Button(
            'Confirm Abandon',
            on_click=self.confirm_abandon,
            disabled=True,
            style=ft.ButtonStyle(color=ft.Colors.RED_400),
        )

        self.progress_ring = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)

        super(AbandonIdentifierDialog, self).__init__(
            modal=True,
            title=ft.Text('Abandon Identifier'),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_400, size=48),
                        ft.Text(
                            'You are about to ROTATE TO NO NEXT KEYS.',
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_400,
                        ),
                        ft.Divider(),
                        ft.Text('This rotation will set:', weight=ft.FontWeight.W_500),
                        ft.Text('  • Next Key Count (ncount) = 0'),
                        ft.Text('  • Next Signing Threshold (nsith) = 0'),
                        ft.Divider(),
                        ft.Text('After this rotation:', weight=ft.FontWeight.W_500),
                        ft.Text('  • The identifier cannot sign anything new'),
                        ft.Text('  • No further rotations are possible'),
                        ft.Text('  • Associated credentials become unusable'),
                        ft.Text('  • This action CANNOT be reversed'),
                        ft.Divider(),
                        self.confirm_checkbox,
                        self.progress_ring,
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=400,
            ),
            actions=[
                ft.OutlinedButton('Cancel', on_click=self.close_dialog),
                self.btn_confirm,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def toggle_confirm_button(self, e):
        """Enable/disable confirm button based on checkbox state."""
        self.btn_confirm.disabled = not self.confirm_checkbox.value
        self.btn_confirm.update()

    async def open_confirm(self, hab):
        """Open the confirmation dialog for the given hab."""
        self.hab = hab
        self.confirm_checkbox.value = False
        self.btn_confirm.disabled = True
        self.progress_ring.visible = False
        self.app.page.show_dialog(self)

    async def close_dialog(self, _):
        """Close the dialog."""
        self.app.page.pop_dialog()

    @log_errors
    async def confirm_abandon(self, e):
        """
        Execute the abandon operation.

        For singlesig identifiers, this directly rotates to null keys.
        For multisig identifiers, this initiates a rotation request
        that requires approval from other participants.
        """
        if not self.hab:
            return

        self.progress_ring.visible = True
        self.btn_confirm.disabled = True
        self.update()

        try:
            if isinstance(self.hab, habbing.GroupHab):
                await self.abandon_group_identifier()
            else:
                await self.abandon_singlesig_identifier()

        except Exception as ex:
            logger.exception('Error abandoning identifier')
            await self.app.snack(f'Error: {str(ex)}')
            self.progress_ring.visible = False
            self.btn_confirm.disabled = False
            self.update()

    async def abandon_singlesig_identifier(self):
        """Abandon a single-sig identifier by rotating to null keys."""
        try:
            # Rotate to null keys - no next keys means abandoned
            self.hab.rotate(ncount=0, nsith='0')

            await self.app.snack(f'Identifier "{self.hab.name}" has been abandoned (rotated to no next keys)')
            logger.info(f'Abandoned identifier {self.hab.name} ({self.hab.pre})')

            # Close dialog
            self.app.page.pop_dialog()

            # Navigate to identifier list
            await self.app.page.push_route('/identifiers')

        except Exception as ex:
            logger.exception('Error abandoning singlesig identifier')
            raise

    async def abandon_group_identifier(self):
        """
        Initiate abandonment for a group identifier.

        This sends a rotation request to other participants.
        All participants must approve the rotation to null keys.
        """
        try:
            ghab = self.hab
            mhab = ghab.mhab

            # Get current signing members
            smids = ghab.db.signingMembers(pre=ghab.pre)
            smids.remove(mhab.pre)

            # For group rotation with null keys, we initiate a rotation event
            # with ncount=0 and nsith='0' and send to other members
            rot = ghab.rotate(ncount=0, nsith='0')
            rserder = serdering.SerderKERI(raw=rot)

            # Send rotation request to other group members
            for recp in smids:
                exn, atc = grouping.multisigRotateExn(ghab=ghab, rot=rserder.raw, smids=smids)
                self.app.agent.postman.send(src=mhab.pre, dest=recp, topic='multisig', serder=exn, attachment=atc)

            await self.app.snack(f'Abandon request sent for "{self.hab.name}". Waiting for other participants to approve...')
            logger.info(f'Initiated abandon for group identifier {self.hab.name} ({self.hab.pre})')

            # Close dialog
            self.app.page.pop_dialog()

            # Navigate to identifier list
            await self.app.page.push_route('/identifiers')

        except Exception as ex:
            logger.exception('Error initiating group identifier abandonment')
            raise
