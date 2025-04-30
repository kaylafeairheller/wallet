"""
Home module for the application.
"""

import logging
import logging

import flet as ft
from flet_core import padding

logger = logging.getLogger('wallet')


class HomeBase(ft.Column):
    """
    Base class for home page.

    Args:
        app: The application object.
        panel: The panel object.
        title (ft.Row): The title panel.

    Attributes:
        app: The application object.
        panel: The panel object.
        card: The container for the panel.
    """

    def __init__(self, app, panel, title=None):
        self.app = app
        title = title if title else ft.Row()
        self.panel = panel
        self.card = ft.Container(
            content=self.panel,
            expand=True,
            alignment=ft.alignment.top_left,
        )

        super().__init__(
            [
                title,
                ft.Row([self.card]),
            ],
            expand=True,
            scroll=ft.ScrollMode.ALWAYS,
        )


class Home(HomeBase):
    def __init__(self, app):
        self.app = app
        self.buttons = ft.Column(
            [
                ft.ElevatedButton(text="Create Group Multisig", on_click=self.create_group_multisig),
            ],
            spacing=10,
            expand=True,
        )

        super().__init__(app, ft.Container(content=self.buttons, padding=padding.only(bottom=125)))

    def did_mount(self):
        self.page.update()

    async def create_group_multisig(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/identifiers/create/default'
