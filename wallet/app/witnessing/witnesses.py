"""
Identifiers module for the Wallet application.
"""

import datetime
import logging

import flet as ft
from keri.app import connecting

from wallet.app.witnessing.witness import WitnessBase
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class Witnesses(WitnessBase):
    """
    Class representing witnesses in the application.

    Attributes:
        page (ft.Page): The page object associated with the app.
        list (ft.Column): The column object representing the list of witnesses.
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
        self.page.run_task(self.refresh_witnesses)

    async def refresh_witnesses(self):
        """
        Refreshes the witnesses
        """
        org = connecting.Organizer(hby=self.app.agent.hby)
        await self.set_witnesses(org.list())
        self.page.update()

    async def add_witness(self, _):
        """
        Adds an identifier to the application.

        This method sets the route to "/witnesses/create" and updates the page asynchronously.

        Parameters:
        - _: Placeholder parameter (unused)

        Returns:
        - None
        """
        await self.app.page.push_route('/witnesses/create')
        self.app.page.update()

    @log_errors
    async def set_witnesses(self, contacts):
        """
        Sets the witnesses for the given list of contacts.

        Args:
            contacts (list): A list of habs to set identifiers for.

        Returns:
            None
        """
        contacts = sorted(contacts, key=lambda c: c.get('alias', c['id']).lower())
        contacts = list(filter(lambda c: 'tag=witness' in c['oobi'], contacts))

        self.list.controls.clear()

        if len(contacts) == 0:
            self.list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.VISIBILITY_OFF_OUTLINED, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text('No witnesses yet', size=18, weight=ft.FontWeight.W_500),
                            ft.Text('Add witnesses to support your identifiers', size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=ft.Padding.all(40),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            )
        else:
            for contact in contacts:
                pre = contact['id']
                logger.debug(f'Processing witness contact: {pre}')
                kever = self.app.agent.hby.kevers[pre]

                dt = None
                if 'last-refresh' in contact:
                    dt = datetime.datetime.fromisoformat(contact['last-refresh'])
                elif kever and kever.dater:
                    dt = datetime.datetime.fromisoformat(f'{kever.dater.dts}')
                sn = None
                if kever and kever.sner:
                    sn = kever.sn

                title = ft.Text(contact['alias'])
                if dt is not None and sn is not None:
                    title = ft.Text(f'{contact["alias"]}')

                tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.SQUARE, tooltip='Witness'),
                    title=title,
                    subtitle=ft.Text(contact['id'], font_family='monospace'),
                    trailing=ft.PopupMenuButton(
                        tooltip=None,
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Text('View'), icon=ft.Icons.PAGEVIEW, on_click=self.view_witness, data=pre
                            ),
                            ft.PopupMenuItem(
                                content=ft.Text('Delete'),
                                icon=ft.Icons.DELETE_FOREVER,
                                on_click=self.delete_witness,
                                data=contact,
                            ),
                        ],
                    ),
                    on_click=self.view_witness,
                    data=pre,
                    shape=ft.StadiumBorder(),
                )
                self.list.controls.append(
                    ft.Container(
                        content=tile,
                    )
                )
                self.list.controls.append(ft.Divider(opacity=0.1))

        self.update()

    @log_errors
    async def view_witness(self, e):
        await self.app.page.push_route(f'/witnesses/{e.control.data}/view')

    @log_errors
    async def delete_witness(self, e):
        """
        Delete a witness from the contacts list.

        Checks if any identifier is currently using this witness before
        allowing deletion. Shows a warning dialog if the witness is in use.

        Args:
            e: The event object containing the witness contact data.

        Returns:
            None
        """
        witness = e.control.data
        wit_pre = witness['id']
        wit_alias = witness.get('alias', wit_pre)

        # Check if any hab uses this witness
        using_habs = []
        for hab in self.app.hby.habs.values():
            if wit_pre in hab.kever.wits:
                using_habs.append(hab.name)

        if using_habs:
            # Show warning dialog - cannot delete witness in use
            hab_list = ', '.join(using_habs)

            async def close_dialog(e):
                self.app.page.pop_dialog()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text('Cannot Delete Witness'),
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400, size=48),
                        ft.Text(f'The witness "{wit_alias}" is currently in use by:'),
                        ft.Text(''),
                        ft.Text(hab_list, weight=ft.FontWeight.BOLD),
                        ft.Text(''),
                        ft.Text('To delete this witness, first rotate these identifiers'),
                        ft.Text('to remove this witness from their witness pool,'),
                        ft.Text('or abandon the identifiers.'),
                    ],
                    tight=True,
                ),
                actions=[
                    ft.Button('OK', on_click=close_dialog),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.app.page.show_dialog(dialog)
            return

        # Show confirmation dialog for deletion
        async def close_dialog(e):
            self.app.page.pop_dialog()

        async def confirm_delete(e):
            self.app.page.pop_dialog()
            await self._perform_witness_deletion(witness)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('Delete Witness'),
            content=ft.Column(
                [
                    ft.Text(f'Are you sure you want to delete the witness "{wit_alias}"?'),
                    ft.Text(''),
                    ft.Text(f'Prefix: {wit_pre}', font_family='monospace', size=12),
                    ft.Text(''),
                    ft.Text('This will remove the witness from your contacts.'),
                ],
                tight=True,
            ),
            actions=[
                ft.OutlinedButton('Cancel', on_click=close_dialog),
                ft.Button('Delete', on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.app.page.show_dialog(dialog)

    async def _perform_witness_deletion(self, witness):
        """
        Perform the actual witness deletion.

        Args:
            witness: The witness contact to delete.
        """
        try:
            org = connecting.Organizer(hby=self.app.agent.hby)
            org.rem(witness['id'])

            await self.app.snack(f'Witness "{witness.get("alias", witness["id"])}" deleted')
            await self.refresh_witnesses()

        except Exception as ex:
            logger.exception('Error deleting witness')
            await self.app.snack(f'Error deleting witness: {str(ex)}')
