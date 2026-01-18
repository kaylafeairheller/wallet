"""
Home module for the application.
"""

import logging

import flet as ft
from flet import Padding

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
            alignment=ft.Alignment.TOP_LEFT,
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
        self.sections = []  # Store references for accordion behavior

        def make_tile(title, subtitle, button_text, handler):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text(title, size=16, weight=ft.FontWeight.W_500),
                        ft.Text(subtitle, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                        ft.Button(content=ft.Text(button_text), on_click=handler),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                ),
                padding=15,
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border_radius=10,
                width=260,
                height=120,
            )

        def make_section_header(title, icon, description):
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, size=24, color=ft.Colors.PRIMARY),
                        ft.Column(
                            [
                                ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                                ft.Text(description, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=10,
                ),
                padding=ft.Padding.only(left=5, top=10, bottom=5),
            )

        # General/Setup Section
        self.setup_section = ft.ExpansionTile(
            title=ft.Text('Setup & Configuration', weight=ft.FontWeight.BOLD),
            subtitle=ft.Text('Create identifiers, contacts, and registries'),
            leading=ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.PRIMARY),
            expanded=True,
            on_change=self.handle_accordion,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    make_tile(
                                        'Create Singlesig', 'Single-signature identifier', 'Create', self.create_singlesig
                                    ),
                                    make_tile('Create Contact', 'Add external contacts', 'Create', self.create_contact),
                                    make_tile('Create Multisig', 'Multi-signature group', 'Create', self.create_multisig),
                                ],
                                spacing=15,
                                wrap=True,
                            ),
                            ft.Row(
                                [
                                    make_tile('Create Registry', 'Credential registry', 'Create', self.create_registry),
                                ],
                                spacing=15,
                            ),
                        ],
                        spacing=15,
                    ),
                    padding=ft.Padding.only(left=15, right=15, bottom=15),
                ),
            ],
        )

        # GEDA Section (GLEIF External GARs)
        self.geda_section = ft.ExpansionTile(
            title=ft.Text('GEDA Actions', weight=ft.FontWeight.BOLD),
            subtitle=ft.Text('GLEIF External Delegated AID Representative'),
            leading=ft.Icon(ft.Icons.VERIFIED_USER, color=ft.Colors.TERTIARY),
            expanded=False,
            on_change=self.handle_accordion,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'As a GEDA, you can issue QVI credentials to Qualified vLEI Issuers.',
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Row(
                                [
                                    make_tile(
                                        'Issue QVI Credential', 'Qualified vLEI Issuer credential', 'Issue', self.issue_qvi
                                    ),
                                ],
                                spacing=15,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.only(left=15, right=15, bottom=15),
                ),
            ],
        )

        # QVI Section (Qualified vLEI Issuers)
        self.qvi_section = ft.ExpansionTile(
            title=ft.Text('QVI Actions', weight=ft.FontWeight.BOLD),
            subtitle=ft.Text('Qualified vLEI Issuer'),
            leading=ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.SECONDARY),
            expanded=False,
            on_change=self.handle_accordion,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'As a QVI, you can issue LE credentials and chain-end credentials (ECR/OOR).',
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Row(
                                [
                                    make_tile(
                                        'Issue LE Credential', 'Legal Entity credential', 'Issue', self.issue_le_credential
                                    ),
                                ],
                                spacing=15,
                            ),
                            ft.Divider(opacity=0.3),
                            ft.Text(
                                'Issue chain-end credentials based on authorizations from Legal Entities:',
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Row(
                                [
                                    make_tile(
                                        'Issue ECR Credential', 'Engagement Context Role', 'Issue', self.issue_ecr_credential
                                    ),
                                    make_tile(
                                        'Issue OOR Credential',
                                        'Official Organizational Role',
                                        'Issue',
                                        self.issue_oor_credential,
                                    ),
                                ],
                                spacing=15,
                                wrap=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.only(left=15, right=15, bottom=15),
                ),
            ],
        )

        # LE Section (Legal Entities)
        self.le_section = ft.ExpansionTile(
            title=ft.Text('LE Actions', weight=ft.FontWeight.BOLD),
            subtitle=ft.Text('Legal Entity'),
            leading=ft.Icon(ft.Icons.CORPORATE_FARE, color=ft.Colors.ERROR),
            expanded=False,
            on_change=self.handle_accordion,
            controls=[
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'As a Legal Entity, you can issue authorization credentials for persons in your organization.',
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Row(
                                [
                                    make_tile('Issue ECR Auth', 'ECR Authorization', 'Issue', self.issue_ecr_auth),
                                    make_tile('Issue OOR Auth', 'OOR Authorization', 'Issue', self.issue_oor_auth),
                                ],
                                spacing=15,
                                wrap=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.Padding.only(left=15, right=15, bottom=15),
                ),
            ],
        )

        # Store all sections for accordion behavior
        self.sections = [self.setup_section, self.geda_section, self.qvi_section, self.le_section]

        layout = ft.Column(
            [
                self.setup_section,
                self.geda_section,
                self.qvi_section,
                self.le_section,
            ],
            spacing=10,
            expand=True,
        )

        super().__init__(app, ft.Container(content=layout, padding=Padding.only(bottom=125)))

    async def handle_accordion(self, e):
        """Close other sections when one is expanded (accordion behavior)."""
        # Check if this section was expanded
        if e.control.expanded:
            for section in self.sections:
                if section != e.control:
                    section.expanded = False
                    section.update()
            self.app.page.update()

    def did_mount(self):
        self.page.update()

    async def create_singlesig(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/singlesig/identifiers/create')

    async def create_contact(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/contacts/create')

    async def create_multisig(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/multisig/identifiers/create')

    async def create_registry(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/registry/create')

    async def issue_qvi(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/issue/qvi_credential')

    async def issue_le_credential(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/issue/le_credential')

    async def issue_ecr_auth(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/issue/ecr_auth')

    async def issue_oor_auth(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/issue/oor_auth')

    async def issue_ecr_credential(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/issue/ecr_credential')

    async def issue_oor_credential(self, e):
        logger.debug(f'Beginning workflow: {e.control.content.value}')
        await self.app.page.push_route('/workflows/issue/oor_credential')
