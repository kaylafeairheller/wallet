import logging

import flet as ft
from flet import FontWeight, Padding
from keri.app import connecting, habbing

from wallet.app.workflows.issuing.issuer import SCHEMA_ECR_AUTH, SCHEMA_LE, IssuerBase
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class CreateIssueECRAuthPanel(IssuerBase):
    """
    CreateIssueECRAuthPanel class for issuing ECR Auth.
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

        self.leCredentialsDropdown = ft.Dropdown(
            options=IssuerBase.loadCredentialsBySchema(self.app.agent, SCHEMA_LE),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
            on_select=self.on_le_credential_selected,
        )

        self.contactsDropdown = ft.Dropdown(
            options=IssuerBase.loadContacts(self.org),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
            on_select=self.save_selection,
        )

        self.personLegalNameTextField = ft.TextField(
            label='Enter requested person legal name:',
            width=550,
            text_size=14,
        )

        self.engagementContextRoleTextField = ft.TextField(
            label='Enter requested engagement context role:',
            width=550,
            text_size=14,
        )

        self.leiTextField = ft.TextField(
            label='LEI',
            width=550,
            text_size=14,
            read_only=True,
        )

        self.panel_ref = self.panel()
        super(CreateIssueECRAuthPanel, self).__init__(app, self.panel_ref)

    def save_selection(self, e: ft.ControlEvent):
        selected_value = e.control.value
        logger.debug(f'User selected: {selected_value}')

    def on_le_credential_selected(self, e: ft.ControlEvent):
        """Handle LE credential selection to auto-populate LEI."""
        selected_said = e.control.value
        logger.debug(f'LE credential selected: {selected_said}')

        # Find the credential data and extract LEI
        for option in self.leCredentialsDropdown.options:
            if option.key == selected_said and option.data:
                lei = option.data.attrib.get('LEI', '')
                self.leiTextField.value = lei
                self.leiTextField.update()
                break

    def validate_form(self) -> tuple:
        """Validate all required fields are filled.

        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not self.issuerDropdown.value:
            return (False, 'Please select an issuer')
        if not self.registryDropdown.value:
            return (False, 'Please select a registry')
        if not self.leCredentialsDropdown.value:
            return (False, 'Please select an LE credential for the edge')
        if not self.contactsDropdown.value:
            return (False, 'Please select a recipient')
        if not self.personLegalNameTextField.value:
            return (False, "Please enter the person's legal name")
        if not self.engagementContextRoleTextField.value:
            return (False, 'Please enter the engagement context role')
        return (True, None)

    def panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Issue ECR Authorization',
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
                                        'Select LE Credential for Edge',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.leCredentialsDropdown,
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
                                        'LEI (from LE Credential)',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.leiTextField,
                                ],
                            ),
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Enter requested person legal name:',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.personLegalNameTextField,
                                ],
                            ),
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Enter requested engagement context role:',
                                        weight=FontWeight.BOLD,
                                    ),
                                ]
                            ),
                            ft.Row(
                                controls=[
                                    self.engagementContextRoleTextField,
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

        await self.app.snack('Issuing ECR Authorization...')

        # Build credential data
        data = {
            'LEI': self.leiTextField.value,
            'personLegalName': self.personLegalNameTextField.value,
            'engagementContextRole': self.engagementContextRoleTextField.value,
        }

        # Build source edge referencing the LE credential
        source = {
            'le': {
                'n': self.leCredentialsDropdown.value,
                's': SCHEMA_LE,
            }
        }

        # Issue the credential
        creder, success, error = await IssuerBase.issue_credential(
            app=self.app,
            registry_key=self.registryDropdown.value,
            recipient=self.contactsDropdown.value,
            schema=SCHEMA_ECR_AUTH,
            data=data,
            source=source,
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
            await self.app.snack('ECR Authorization issued successfully!')
            await self.app.page.push_route('/credentials')
        else:
            await self.app.snack('Credential issuance timed out. Check notifications for status.')

    async def cancel(self, _):
        await self.app.page.push_route('/home')
