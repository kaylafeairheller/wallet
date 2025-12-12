import logging

import flet as ft
from flet_core import FontWeight, padding
from keri.app import connecting

from wallet.app.workflows.issuing.issuer import IssuerBase

logger = logging.getLogger('wallet')


class CreateIssueQVIPanel(IssuerBase):
    """
    CreateIssueQVIPanel class for issuing ECR Auth.
    """

    def __init__(self, app):
        self.app = app
        self.org = connecting.Organizer(hby=app.agent.hby)

        self.issuerDropdown = ft.Dropdown(
            options=IssuerBase.loadIssuers(self.app.agent),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
            on_change=self.save_selection,
        )

        self.registryDropdown = ft.Dropdown(
            options=IssuerBase.loadRegistries(),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
            on_change=self.save_selection,
        )

        self.contactsDropdown = ft.Dropdown(
            options=IssuerBase.loadContacts(self.org),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
            on_change=self.save_selection,
        )

        self.qviLEI = ft.TextField(
            label='LEI',
            hint_text='LEI of QVI',
        )

        self.panel_ref = self.panel()
        super(CreateIssueQVIPanel, self).__init__(app, self.panel_ref)

    def save_selection(self, e: ft.ControlEvent):
        selected_value = e.control.value
        print(f"User selected: {selected_value}")
    
    def panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Issue QVI Credential',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Select Issuer',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.issuerDropdown,
                                ],
                            )
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Select Registry',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.registryDropdown,
                                ],
                            )
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Select recipient',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.contactsDropdown,
                                ],
                            )
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Enter LEI of QVI',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.qviLEI,
                                ],
                            )
                        ]
                    ),                    
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                'Issue',
                                on_click=self.issue,
                            ),
                            ft.ElevatedButton(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ],
            ),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=padding.only(bottom=105),
        )
    
    async def issue(self, _):
        await self.app.snack(f'Issuing QVI Credential...')
        self.app.page.route = f'/home'
        await self.page.update_async()

    async def cancel(self, _):
        self.app.page.route = '/home'
        await self.page.update_async()
