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
                self.card,
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
                    ft.Text(title, style="titleMedium"),
                    ft.ElevatedButton(text=button_text, on_click=handler)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10),
                padding=15,
                bgcolor=ft.colors.SURFACE_VARIANT,
                border_radius=10,
                width=260,
                height=110,
            )

        row1 = ft.Row([
            make_tile("Create Singlesig Identifier", "For individuals", "Create", self.create_singlesig),
            make_tile("Create Contact", "Create a contact to use in multsig identifier", "Create", self.create_contact),
            make_tile("Create Multisig Identifier", "For multisig groups", "Create", self.create_multisig),
        ], spacing=15, )

        row2 = ft.Row([
            make_tile("Create Registry", "Create registry inn order to issue credentials", "Create", self.create_registry),
        ], spacing=15, )

        row3 = ft.Row([
            make_tile("Issue QVI Credential", "Qualified vLEI Issuer", "Issue", self.issue_qvi),
            ft.Container(
                content=ft.Icon(ft.icons.ARROW_FORWARD, size=36, color=ft.colors.ON_SURFACE_VARIANT),
                alignment=ft.alignment.center,
            ),
            make_tile("Issue LE Credential", "Qualified vLEI Issuer", "Issue", self.issue_le_credential),
        ], spacing=15)

        row4 = ft.Row([
            make_tile("Issue OOR Authorization", "Organizational Official Role", "Issue", self.issue_oor_auth),
            ft.Container(
                content=ft.Icon(ft.icons.ARROW_FORWARD, size=36, color=ft.colors.ON_SURFACE_VARIANT),
                alignment=ft.alignment.center,
            ),
            make_tile("Issue OOR Credential", "Organizational Official Role", "Issue", self.issue_oor_credential),
        ], spacing=15)

        row5 = ft.Row([
            make_tile("Issue ECR Authorization", "Entity Credentials Registry", "Issue", self.issue_ecr_auth),
            ft.Container(
                content=ft.Icon(ft.icons.ARROW_FORWARD, size=36, color=ft.colors.ON_SURFACE_VARIANT),
                alignment=ft.alignment.center,
            ),
            make_tile("Issue ECR Credential", "Entity Credentials Registry", "Issue", self.issue_ecr_credential),
        ], spacing=15)

        layout = ft.Column([row1, row2, row3, row4, row5], spacing=15, expand=True)

        super().__init__(app, ft.Container(content=layout, padding=padding.only(bottom=125)))

    def did_mount(self):
        self.page.update()

    async def create_singlesig(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/singlesig/identifiers/create'

    async def create_contact(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/contacts/create'

    async def create_multisig(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/multisig/identifiers/create'
    
    async def create_registry(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/registry/create'

    async def issue_qvi(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/qvi_credential'

    async def issue_le_credential(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/le_credential'

    async def issue_ecr_auth(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/ecr_auth'

    async def issue_oor_auth(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/oor_auth'

    async def issue_ecr_credential(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/ecr_credential'

    async def issue_oor_credential(self, e):
        print(f"Beginning {e.control.text}")
        self.app.page.route = '/workflows/issue/oor_credential'