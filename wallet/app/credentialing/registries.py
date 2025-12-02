"""
Registries module for the Wallet application.
"""

import logging
import pprint

import flet as ft

from wallet.app import colouring
from wallet.app.credentialing.registry import RegistryBase
from wallet.app.identifying.identifiers import Identifiers
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
        self.page: ft.Page = app.page
        self.list = ft.Column([], spacing=0, expand=True)

        super().__init__(app, ft.Container(content=self.list, padding=ft.padding.only(bottom=125)))

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
        for aid, rgy in self.app.agent.rgy.regs.items():
            tip = 'Registry'
            icon = ft.icons.FOLDER_OPEN

            view = ft.PopupMenuItem(text='View', icon=ft.icons.PAGEVIEW, on_click=self.view_registry)
            view.data = rgy
            delete = ft.PopupMenuItem(
                text='Delete',
                icon=ft.icons.DELETE_FOREVER,
                on_click=print('delete!'),
            )
            delete.data = rgy

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
                    icon=ft.icons.MORE_VERT,
                    items=[
                        view,
                        delete,
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

        await self.update_async()

    async def view_registry(self, e):
        """
        View the registry details.

        Args:
            e: The event object containing the registry data.

        Returns:
            None
        """
        rgy = e.control.data
        pprint.pprint({"REGISTRY": rgy.__dict__})
        pprint.pprint({"GROUP MULTISIG": rgy.hab.__dict__})
        self.app.page.route = f'/registries/{rgy.regk}/view'
        await self.app.page.update_async()
