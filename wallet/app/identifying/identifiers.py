"""
Identifiers module for the Wallet application.
"""

import logging

import flet as ft
from keri.app import habbing

from wallet.app import colouring
from wallet.app.identifying.abandon_confirm import AbandonIdentifierDialog
from wallet.app.identifying.identifier import IdentifierBase
from wallet.app.identifying.kel_update_confirm import KELUpdateConfirmDialog
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class Identifiers(IdentifierBase):
    """
    Class representing identifiers in the application.

    Attributes:
        page (ft.Page): The page object associated with the app.
        list (ft.Column): The column object representing the list of identifiers.
    """

    def __init__(self, app):
        self._page: ft.Page = app.page  # Store page reference (page property is read-only in Flet controls)
        self.list = ft.Column([], spacing=0, expand=True)
        self.kel_update_dialog = None
        self.hide_abandoned = True  # Default to hiding abandoned identifiers

        self.filter_checkbox = ft.Checkbox(
            label='Hide abandoned',
            value=self.hide_abandoned,
            on_change=self.toggle_filter,
        )

        self.filter_row = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.FILTER_LIST, size=16),
                    self.filter_checkbox,
                ],
                spacing=5,
            ),
            padding=ft.Padding.only(left=10, bottom=5),
        )

        content = ft.Column(
            [
                self.filter_row,
                self.list,
            ],
            spacing=0,
            expand=True,
        )

        super().__init__(app, ft.Container(content=content, padding=ft.Padding.only(bottom=125)))

    @property
    def page(self):
        return self._page

    def did_mount(self):
        self.page.run_task(self.refresh_identifiers)

    async def toggle_filter(self, e):
        """Toggle the hide abandoned filter and refresh the list."""
        self.hide_abandoned = self.filter_checkbox.value
        await self.refresh_identifiers()

    @staticmethod
    def get_habs(agent):
        """Get the Hab instances an agent has."""
        return agent.hby.habs.values()

    @staticmethod
    def get_identifier(agent, aid):
        for hab in agent.hby.habs.values():
            if hab.pre == aid:
                return hab

    @staticmethod
    def get_aids(agent):
        """Get the identifiers (AID prefixes) an agent has."""
        return [hab.pre for hab in Identifiers.get_habs(agent)]

    async def refresh_identifiers(self):
        """
        Refreshes the identifiers by setting them to the current list of HABs and updating the state.
        """
        await self.set_identifiers(self.get_habs(self.app.agent))
        self.update()

    async def add_identifier(self, _):
        """
        Adds an identifier to the application.

        This method sets the route to "/identifiers/create" and updates the page asynchronously.

        Parameters:
        - _: Placeholder parameter (unused)

        Returns:
        - None
        """
        await self.app.page.push_route('/identifiers/create')
        self.app.page.update()

    def check_aid_updates(self, pre):
        for update in self.app.agent.aid_updates:
            if update.aid == pre:
                return True, update
        return False, None

    @log_errors
    async def kel_update(self, e):
        """
        Updates a local AID, usually multisig, from the specified witness
        Parameters:
            aid_update (AidKelUpdate): Contains the AID and witness information needed to update the
                local KEL from the witness specified
        """
        hab, aid_update = e.control.data
        dialog = KELUpdateConfirmDialog(self.app)
        self.page.dialog = dialog
        await dialog.open_confirm(hab, aid_update)

    @log_errors
    async def set_identifiers(self, habs):
        """
        Sets the identifiers for the given list of habs.

        Args:
            habs (list): A list of habs to set identifiers for.

        Returns:
            None
        """
        self.list.controls.clear()

        # Convert to list and sort alphabetically by name
        habs = sorted(list(habs), key=lambda h: h.name.lower())

        # Count abandoned for filter visibility
        abandoned_count = sum(1 for hab in habs if len(hab.kever.ndigers) == 0)
        total_count = len(habs)

        # Show/hide filter based on whether there are any abandoned
        self.filter_row.visible = abandoned_count > 0

        # Apply filter if enabled
        if self.hide_abandoned:
            habs = [hab for hab in habs if len(hab.kever.ndigers) > 0]

        # Update filter label to show counts
        if abandoned_count > 0:
            self.filter_checkbox.label = (
                f'Hide abandoned ({abandoned_count} hidden)'
                if self.hide_abandoned
                else f'Hide abandoned ({abandoned_count} abandoned)'
            )
            self.filter_checkbox.update()

        if len(habs) == 0:
            if total_count == 0:
                # No identifiers at all
                self.list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.FINGERPRINT, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
                                ft.Text('No identifiers yet', size=18, weight=ft.FontWeight.W_500),
                                ft.Text('Create an identifier to get started', size=14, color=ft.Colors.ON_SURFACE_VARIANT),
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
                # All identifiers are filtered out (all abandoned)
                self.list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(ft.Icons.FILTER_LIST_OFF, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
                                ft.Text('All identifiers are hidden', size=18, weight=ft.FontWeight.W_500),
                                ft.Text(
                                    f'{abandoned_count} abandoned identifier{"s" if abandoned_count != 1 else ""} filtered out',
                                    size=14,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Text('Uncheck "Hide abandoned" to show them', size=14, color=ft.Colors.ON_SURFACE_VARIANT),
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
            for hab in habs:
                needs_update, aid_update = self.check_aid_updates(hab.pre)
                tip = 'Identifier'

                # Check if identifier is abandoned (no next keys)
                is_abandoned = len(hab.kever.ndigers) == 0

                if isinstance(hab, habbing.GroupHab):
                    icon = ft.Icons.DATASET_LINKED_OUTLINED
                elif isinstance(hab, habbing.Hab):  # GroupHab does not have .algo prop
                    icon = ft.Icons.LINK_OUTLINED
                else:
                    logger.error('Unknown hab type: %s', type(hab))
                    raise ValueError(f'Unknown hab type: {type(hab)}')

                # Override icon if abandoned
                if is_abandoned:
                    icon = ft.Icons.BLOCK
                    tip = 'Abandoned Identifier'

                # Bug in FLET that doesn't set `data` in constructor
                view = ft.PopupMenuItem(content=ft.Text('View'), icon=ft.Icons.PAGEVIEW, on_click=self.view_identifier)
                view.data = hab

                # Build menu items - only show rotate/abandon if not already abandoned
                menu_items = [view]
                if not is_abandoned:
                    rotate = ft.PopupMenuItem(
                        content=ft.Text('Rotate'),
                        icon=ft.Icons.ROTATE_RIGHT,
                        on_click=self.rotate_identifier,
                    )
                    rotate.data = hab
                    abandon = ft.PopupMenuItem(
                        content=ft.Text('Abandon'),
                        icon=ft.Icons.BLOCK,
                        on_click=self.abandon_identifier,
                    )
                    abandon.data = hab
                    menu_items.extend([rotate, abandon])

                title_row = ft.Row(
                    [
                        ft.Text(
                            hab.pre,
                            font_family='monospace',
                        ),
                    ]
                )

                # Show abandoned badge
                if is_abandoned:
                    title_row.controls.append(
                        ft.Container(
                            content=ft.Text('ABANDONED', size=10, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.RED_400,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                            border_radius=3,
                        )
                    )

                if needs_update:
                    title_row.controls.append(ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, tooltip='AID needs to be caught up.'))
                    title_row.controls.append(
                        ft.OutlinedButton(content='Update Log', data=(hab, aid_update), on_click=self.kel_update)
                    )
                tile = ft.ListTile(
                    leading=ft.Icon(
                        icon,
                        tooltip=tip,
                        color=ft.Colors.RED_400 if is_abandoned else None,
                    ),
                    title=ft.Text(
                        value=hab.name,
                        color=ft.Colors.RED_400 if is_abandoned else colouring.Colouring.get(colouring.Colouring.ON_SURFACE),
                    ),
                    subtitle=title_row,
                    trailing=ft.PopupMenuButton(
                        tooltip=None,
                        icon=ft.Icons.MORE_VERT,
                        items=menu_items,
                    ),
                    on_click=self.view_identifier,
                    data=hab,
                    shape=ft.StadiumBorder(),
                )
                self.list.controls.append(
                    ft.Container(
                        content=tile,
                    )
                )
                self.list.controls.append(ft.Divider(opacity=0.1))

        self.update()

    async def view_identifier(self, e):
        """
        View the identifier details.

        Args:
            e: The event object containing the identifier data.

        Returns:
            None
        """
        hab = e.control.data
        await self.app.page.push_route(f'/identifiers/{hab.pre}/view')

    async def rotate_identifier(self, e):
        """
        Rotates the identifier associated with the given event.

        Args:
            e (Event): The event containing the identifier to rotate.

        Returns:
            None
        """
        hab = e.control.data
        await self.app.page.push_route(f'/identifiers/{hab.pre}/rotate')

    @log_errors
    async def abandon_identifier(self, e):
        """
        Abandons an identifier by rotating to null keys.

        This is the KERI BADA-RUN approach to nullifying an identifier.
        The identifier will be rotated with ncount=0 and nsith='0',
        making it permanently unusable.

        Args:
            e: The event object containing the identifier data.

        Returns:
            None
        """
        hab = e.control.data
        dialog = AbandonIdentifierDialog(self.app)
        await dialog.open_confirm(hab)
