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

        def make_tile(title, subtitle, button_text, handler):
            return ft.Container(
                content=ft.Column([
                    ft.Text(title, style="headlineSmall"),
                    ft.Text(subtitle, style="bodyMedium"),
                    ft.ElevatedButton(text=button_text, on_click=handler)
                ],
                spacing=10),
                padding=15,
                bgcolor=ft.colors.SURFACE_VARIANT,
                border_radius=10,
                width=300,
                height=180,
            )

        row1 = ft.Row([
            make_tile("Create Singlesig Identifier", "For individuals", "Create Singlesig", self.create_singlesig),
            make_tile("Create Group Multisig Identifier", "For multisig groups", "Create Multisig", self.create_multisig),
        ], spacing=15, )

        row2 = ft.Row([
            make_tile("Accept Delegation", "Accept identifier control from another party", "Accept Delegation", self.accept_delegation),
        ], spacing=15)

        row3 = ft.Row([
            make_tile("Issue QVI Credential", "Qualified vLEI Issuer", "Issue QVI", self.issue_qvi),
            make_tile("Issue OOR Auth Credential", "Organizational Official Role", "Issue OOR Auth", self.issue_oor_auth),
            make_tile("Issue ECR Auth Credential", "Entity Credentials Registry", "Issue ECR Auth", self.issue_ecr_auth),
        ], spacing=15)

        layout = ft.Column([row1, row2, row3], spacing=15, expand=True)

        super().__init__(app, ft.Container(content=layout, padding=padding.only(bottom=125)))

    def did_mount(self):
        self.page.update()

    async def create_singlesig(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/singlesig/identifiers/create'

    async def create_multisig(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/multisig/identifiers/create'

    async def accept_delegation(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/delegation/accept'

    async def issue_qvi(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/qvi'

    async def issue_ecr_auth(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/ecr'

    async def issue_oor_auth(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/oor'