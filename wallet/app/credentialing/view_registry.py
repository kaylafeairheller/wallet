"""
View Registry Panel - Display registry details.
"""

import logging

import flet as ft
import pyperclip
from flet import Padding

from wallet.app.credentialing.registry import RegistryBase
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class ViewRegistryPanel(RegistryBase):
    """Panel for viewing registry details."""

    def __init__(self, app, registry):
        self.app = app
        self.registry = registry
        self.hab = registry.hab

        super(ViewRegistryPanel, self).__init__(
            app=app,
            panel=self.panel(),
            title=ft.Row(
                controls=[
                    ft.Container(
                        ft.Text(value=f'Registry: {self.registry.name}', size=24),
                        padding=Padding.only(left=10, right=10),
                    ),
                    ft.Container(
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=self.close),
                        alignment=ft.Alignment.TOP_RIGHT,
                        expand=True,
                        padding=Padding.only(right=10),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def panel(self):
        """Build the registry detail panel."""
        # Get credential count for this registry
        cred_count = self._get_credential_count()

        # Get configuration safely - these come from tever (transaction event verifier)
        try:
            est_only = self.registry.estOnly if self.registry.tever else False
        except Exception as ex:
            logger.warning(f'Error getting estOnly: {ex}')
            est_only = False

        try:
            no_backers = self.registry.noBackers if self.registry.tever else False
        except Exception as ex:
            logger.warning(f'Error getting noBackers: {ex}')
            no_backers = False

        # Get backers - these are registry-specific (TEL backers), not identifier witnesses
        try:
            baks = self.registry.baks if self.registry.tever else []
        except Exception as ex:
            logger.warning(f'Error getting baks: {ex}')
            baks = []

        # Get backers section (registry-specific TEL backers)
        backers_section = self._build_backers_section(no_backers, baks)

        # Get identifier witnesses for context
        witnesses_section = self._build_witnesses_section()

        return ft.Container(
            ft.Column(
                [
                    # Registry Key
                    ft.Row(
                        [
                            ft.Text('Registry Key:', weight=ft.FontWeight.BOLD, width=175),
                            ft.Text(self.registry.regk or 'N/A', font_family='monospace'),
                            ft.IconButton(
                                icon=ft.Icons.COPY_ROUNDED,
                                data=self.registry.regk or '',
                                on_click=self.copy_to_clipboard,
                                tooltip='Copy Registry Key',
                            ),
                        ]
                    ),
                    # Registry SAID
                    ft.Row(
                        [
                            ft.Text('Registry SAID:', weight=ft.FontWeight.BOLD, width=175),
                            ft.Text(getattr(self.registry, 'regd', 'N/A') or 'N/A', font_family='monospace'),
                            ft.IconButton(
                                icon=ft.Icons.COPY_ROUNDED,
                                data=getattr(self.registry, 'regd', '') or '',
                                on_click=self.copy_to_clipboard,
                                tooltip='Copy Registry SAID',
                            ),
                        ]
                    ),
                    ft.Divider(),
                    # Controlling Identifier Section
                    ft.Text('Controlling Identifier', weight=ft.FontWeight.BOLD, size=16),
                    ft.Row(
                        [
                            ft.Text('Name:', weight=ft.FontWeight.BOLD, width=175),
                            ft.Text(self.hab.name),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text('Prefix:', weight=ft.FontWeight.BOLD, width=175),
                            ft.Text(self.hab.pre, font_family='monospace'),
                            ft.IconButton(
                                icon=ft.Icons.COPY_ROUNDED,
                                data=self.hab.pre,
                                on_click=self.copy_to_clipboard,
                                tooltip='Copy Identifier Prefix',
                            ),
                        ]
                    ),
                    ft.Divider(),
                    # Configuration Section
                    ft.Text('Configuration', weight=ft.FontWeight.BOLD, size=16),
                    ft.Row(
                        [
                            ft.Text('Establishment Only:', weight=ft.FontWeight.BOLD, width=175),
                            ft.Checkbox(
                                value=est_only,
                                disabled=True,
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Text('No TEL Backers:', weight=ft.FontWeight.BOLD, width=175),
                            ft.Checkbox(
                                value=no_backers,
                                disabled=True,
                            ),
                            ft.Text(
                                '(uses identifier witnesses)' if no_backers else '',
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ]
                    ),
                    ft.Divider(),
                    # Identifier Witnesses Section
                    witnesses_section,
                    # Registry Backers Section (if applicable)
                    backers_section,
                    # Credentials Section
                    ft.Text('Credentials', weight=ft.FontWeight.BOLD, size=16),
                    ft.Row(
                        [
                            ft.Text('Issued:', weight=ft.FontWeight.BOLD, width=175),
                            ft.Text(f'{cred_count} credential{"s" if cred_count != 1 else ""}'),
                        ]
                    ),
                    ft.Divider(),
                    # Actions
                    ft.Row(
                        [
                            ft.Button(
                                'Close',
                                on_click=self.close,
                            ),
                        ]
                    ),
                ],
                scroll=ft.ScrollMode.ALWAYS,
            ),
            expand=True,
            alignment=ft.Alignment.TOP_LEFT,
            padding=Padding.only(left=10, bottom=80),
        )

    def _get_credential_count(self):
        """Get the count of credentials issued under this registry."""
        count = 0
        try:
            # Get all credentials and count those belonging to this registry
            for keys, cred in self.app.agent.rgy.reger.creds.getItemIter():
                if cred and hasattr(cred, 'status') and cred.status == self.registry.regk:
                    count += 1
        except Exception as ex:
            logger.warning(f'Error counting credentials: {ex}')
        return count

    def _build_witnesses_section(self):
        """Build the identifier witnesses section."""
        try:
            wits = self.hab.kever.wits if self.hab and self.hab.kever else []
        except Exception as ex:
            logger.warning(f'Error getting witnesses: {ex}')
            wits = []

        if not wits:
            return ft.Column(
                [
                    ft.Text('Identifier Witnesses', weight=ft.FontWeight.BOLD, size=16),
                    ft.Text('No witnesses configured', color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Divider(),
                ]
            )

        witnesses_list = ft.Column(spacing=5)
        for idx, wit in enumerate(wits):
            witnesses_list.controls.append(
                ft.Row(
                    [
                        ft.Text(f'{idx + 1}.', width=30),
                        ft.Text(wit, font_family='monospace'),
                        ft.IconButton(
                            icon=ft.Icons.COPY_ROUNDED,
                            data=wit,
                            on_click=self.copy_to_clipboard,
                            tooltip='Copy Witness Prefix',
                            icon_size=16,
                        ),
                    ]
                )
            )

        return ft.Column(
            [
                ft.Text('Identifier Witnesses', weight=ft.FontWeight.BOLD, size=16),
                ft.Container(content=witnesses_list, padding=Padding.only(left=20)),
                ft.Divider(),
            ]
        )

    def _build_backers_section(self, no_backers, baks):
        """Build the registry backers section (TEL-specific)."""
        if no_backers or not baks:
            return ft.Container()  # Empty container if no backers

        backers_list = ft.Column(spacing=5)
        for idx, backer in enumerate(baks):
            backers_list.controls.append(
                ft.Row(
                    [
                        ft.Text(f'{idx + 1}.', width=30),
                        ft.Text(backer, font_family='monospace'),
                        ft.IconButton(
                            icon=ft.Icons.COPY_ROUNDED,
                            data=backer,
                            on_click=self.copy_to_clipboard,
                            tooltip='Copy Backer Prefix',
                            icon_size=16,
                        ),
                    ]
                )
            )

        return ft.Column(
            [
                ft.Text('Registry TEL Backers', weight=ft.FontWeight.BOLD, size=16),
                ft.Container(content=backers_list, padding=Padding.only(left=20)),
                ft.Divider(),
            ]
        )

    async def close(self, e):
        """Navigate back to registries list."""
        await self.app.page.push_route('/registries')

    async def copy_to_clipboard(self, e):
        """Copy data to clipboard."""
        pyperclip.copy(e.control.data)
        await self.app.snack('Copied to clipboard!', duration=2000)
