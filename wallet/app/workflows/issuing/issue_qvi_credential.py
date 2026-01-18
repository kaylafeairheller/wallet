import logging

import flet as ft
from flet import FontWeight, Padding
from keri.app import connecting, habbing

from wallet.app.workflows.issuing.issuer import SCHEMA_QVI, IssuerBase
from wallet.logs import log_errors

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
            on_select=self.save_selection,
        )

        self.registryDropdown = ft.Dropdown(
            options=IssuerBase.loadRegistries(self.app.agent),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
            on_select=self.save_selection,
        )

        self.contactsDropdown = ft.Dropdown(
            options=IssuerBase.loadContacts(self.org),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
            on_select=self.save_selection,
        )

        self.qviLEI = ft.TextField(
            label='LEI',
            hint_text='LEI of QVI',
        )

        self.panel_ref = self.panel()
        super(CreateIssueQVIPanel, self).__init__(app, self.panel_ref)

    def save_selection(self, e: ft.ControlEvent):
        selected_value = e.control.value
        logger.debug(f'User selected: {selected_value}')

    def validate_form(self) -> tuple:
        """Validate all required fields are filled.

        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not self.issuerDropdown.value:
            return (False, 'Please select an issuer')
        if not self.registryDropdown.value:
            return (False, 'Please select a registry')
        if not self.contactsDropdown.value:
            return (False, 'Please select a recipient')
        if not self.qviLEI.value:
            return (False, 'Please enter the LEI')
        if len(self.qviLEI.value) != 20:
            return (False, 'LEI must be exactly 20 characters')
        return (True, None)

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
                            ),
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
                            ),
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
                            ),
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
                            ),
                        ]
                    ),
                    ft.Row(
                        [
                            ft.Button(
                                'Issue',
                                on_click=self.issue,
                            ),
                            ft.Button(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ],
            ),
            expand=True,
            alignment=ft.Alignment.TOP_LEFT,
            padding=Padding.only(bottom=105),
        )

    @log_errors
    async def issue(self, _):
        # Validate form fields
        is_valid, error_msg = self.validate_form()
        if not is_valid:
            await self.app.snack(error_msg)
            return

        await self.app.snack('Issuing QVI Credential...')

        # Build credential data
        data = {
            'LEI': self.qviLEI.value,
        }

        # Issue the credential
        creder, success, error = await IssuerBase.issue_credential(
            app=self.app,
            registry_key=self.registryDropdown.value,
            recipient=self.contactsDropdown.value,
            schema=SCHEMA_QVI,
            data=data,
            source=None,  # QVI has no edge dependencies
        )

        if not success:
            await self.app.snack(f'Error issuing credential: {error}')
            return

        # Check if this is a multisig - need to wait for other participants
        registry = None
        for reg in self.app.agent.rgy.regs.values():
            if reg.regk == self.registryDropdown.value:
                registry = reg
                break

        if registry and isinstance(registry.hab, habbing.GroupHab):
            await self.app.snack('Credential issuance initiated. Waiting for other participants to approve...')

        # Wait for credential completion
        completed = await IssuerBase.wait_for_completion(self.app, creder.said)

        if completed:
            await self.app.snack('QVI Credential issued successfully!')
            await self.app.page.push_route('/credentials')
        else:
            await self.app.snack('Credential issuance timed out. Check notifications for status.')

    async def cancel(self, _):
        await self.app.page.push_route('/home')
