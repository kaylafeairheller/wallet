"""
Registries module for the Wallet application.
"""

import logging
import pprint

import flet as ft

from wallet.app import colouring
from wallet.app.credentialing.registry import RegistryBase
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class Registries(RegistryBase):
    """
    Class representing registries in the application.

    Attributes:
        page (ft.Page): The page object associated with the app.
        list (ft.Column): The column object representing the list of registries.
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
        self.page.run_task(self.refresh_registries)

    async def refresh_registries(self):
        """
        Refreshes the registries by setting them to the current list.
        """
        await self.set_registries()
        self.update()

    @log_errors
    async def set_registries(self):
        """
        Sets the registries for the list view.
        """
        self.list.controls.clear()

        if not self.app.agent.rgy.regs:
            self.list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.FOLDER_OFF_OUTLINED, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text('No registries yet', size=18, weight=ft.FontWeight.W_500),
                            ft.Text(
                                'Create a registry to start issuing credentials', size=14, color=ft.Colors.ON_SURFACE_VARIANT
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
            return

        # Sort registries alphabetically by name
        sorted_regs = sorted(self.app.agent.rgy.regs.items(), key=lambda x: x[1].name.lower())

        for aid, rgy in sorted_regs:
            tip = 'Registry'
            icon = ft.Icons.FOLDER_OPEN

            view = ft.PopupMenuItem(content=ft.Text('View'), icon=ft.Icons.PAGEVIEW, on_click=self.view_registry)
            view.data = rgy

            title_row = ft.Row(
                [
                    ft.Text(
                        aid,
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
                    value=rgy.name,
                    color=colouring.Colouring.get(colouring.Colouring.ON_SURFACE),
                ),
                subtitle=title_row,
                trailing=ft.PopupMenuButton(
                    tooltip=None,
                    icon=ft.Icons.MORE_VERT,
                    items=[
                        view,
                    ],
                ),
                on_click=self.view_registry,
                data=rgy,
                shape=ft.StadiumBorder(),
            )
            self.list.controls.append(
                ft.Container(
                    content=tile,
                )
            )
            self.list.controls.append(ft.Divider(opacity=0.1))

        self.update()

    async def add_registry(self, _):
        """
        Navigate to the create registry workflow.

        Parameters:
        - _: Placeholder parameter (unused)

        Returns:
        - None
        """
        await self.app.page.push_route('/workflows/registry/create')

    async def view_registry(self, e):
        """
        View the registry details.

        Args:
            e: The event object containing the registry data.

        Returns:
            None
        """
        rgy = e.control.data
        pprint.pprint({'REGISTRY': rgy.__dict__})
        pprint.pprint({'GROUP MULTISIG': rgy.hab.__dict__})
        await self.app.page.push_route(f'/registries/{rgy.regk}/view')
