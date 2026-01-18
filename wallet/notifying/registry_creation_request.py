import asyncio
import logging

import flet as ft
from keri import kering
from keri.core import eventing, serdering

from wallet.app.colouring import Colouring
from wallet.logs import log_errors
from wallet.notifying.notification import NotificationsBase

logger = logging.getLogger('wallet')


class NoticeRegistryCreation(NotificationsBase):
    """
    Represents a notification for a registry creation request.

    Args:
        app (App): The application instance.
        note (Note): The notification object.

    Attributes:
        app (App): The application instance.
        note (Note): The notification object.
        said (str): The notification attribute 'd'.
        mhab (Optional[Habitant]): The member's habitant object.
        ked (Optional[dict]): The cloned KERI event data.
        embeds (Optional[dict]): The embedded data.
        btn_join (ElevatedButton): The 'Join' button.
        group_info_pacifier (Row): The row displaying the fetching notification information message.
        members_list (Column): The column displaying the list of members.
        registry_id (TextField): The text field displaying the group ID.
        registry_name (TextField): The text field for entering the group alias.
        group_info (Column): The column containing the group information.
    """

    def __init__(self, app, note):
        self.app = app
        logger.debug(f'Registry creation note: {note.__dict__}')
        logger.debug(f'Registry creation attrs: {note.attrs}')
        self.note = note
        self.said = note.attrs['d']
        self.mhab = None
        self.ked = None
        self.embeds = None
        self.signing_members = []
        self.rotation_members = []

        self.btn_create = ft.Button(
            'Create',
            on_click=self.create,
            data=note.rid,
            disabled=True,
        )

        self.group_info_pacifier = ft.Row([ft.Text('Fetching notification information...')], visible=True)

        self.members_list = ft.Column([])
        self.ghab_members_list = ft.Column([])

        self.registry_id = ft.TextField(
            label='Registry ID',
            value=note.attrs['d'],
            read_only=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )

        self.registry_name = ft.TextField(label='Enter name', value='')
        self.registry_description = ft.TextField(label='Enter description', value='')

        self.current_threshold = ft.TextField(
            label='Number of current signers required:',
            value='',
            read_only=True,
            visible=False,
        )
        self.next_threshold = ft.TextField(
            label='Number of next signers required:',
            value='',
            read_only=True,
            visible=False,
        )

        self.group_info = ft.Column(
            controls=[
                self.registry_id,
                self.registry_name,
                self.registry_description,
                ft.Divider(),
                ft.Row([ft.Text('Proposed members:')]),
                self.members_list,
            ],
            visible=False,
            width=500,
        )

        super().__init__(
            app,
            self.panel(),
            ft.Row(
                controls=[
                    ft.Container(
                        ft.Text(value='Registry Creation Request', size=24),
                        padding=ft.Padding.only(left=10, top=0, right=10, bottom=0),
                    ),
                    ft.Container(
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=self.cancel),
                        alignment=ft.Alignment.TOP_RIGHT,
                        expand=True,
                        padding=ft.Padding.only(left=0, top=0, right=10, bottom=0),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    async def cancel(self, e):
        await self.app.page.push_route('/notifications')
        self.app.page.update()

    def did_mount(self):
        self.page.run_task(self.get_exchange_message)

    @log_errors
    async def get_exchange_message(self):
        """
        Retrieves the exchange message from the agent's cloner and updates the UI accordingly.

        Returns:
            None
        """
        self.app.agent.cloner.clone(self.said)

        while self.said not in self.app.agent.cloner.cloned:
            await asyncio.sleep(1)

        cloned = self.app.agent.cloner.cloned[self.said]
        logger.debug(f'Cloned exn: {cloned.__dict__}')
        self.ked = cloned.ked

        org = self.app.agent.org

        self.local_identifier = self.ked['i']
        alias = org.get(self.local_identifier)['alias']
        await self.add_member(self.local_identifier, 'Local Identifier', alias)

        self.multisig_gid = self.ked['a']['gid']
        ghab = self.app.agent.hby.habByPre(self.multisig_gid)
        logger.debug(f'Group hab: {ghab.__dict__}')
        await self.add_member(self.multisig_gid, 'Alias', ghab.name)

        self.registry_id.value = self.ked['d']

        self.group_info_pacifier.visible = False
        self.group_info.visible = True
        self.btn_create.disabled = False

        self.update()

        return None

    async def add_member(self, member, label, alias):
        self.members_list.controls.append(
            ft.TextField(
                label=label + ': ' + alias,
                value=member,
                read_only=True,
                text_style=ft.TextStyle(font_family='monospace'),
            )
        )

    def panel(self):
        """
        Creates and returns a panel containing the group inception request information.

        Returns:
            ft.Container: The panel containing the group inception request information.
        """
        return ft.Container(
            ft.Column(
                [
                    self.group_info_pacifier,
                    self.group_info,
                    ft.Row(
                        [
                            self.btn_create,
                            ft.Button('Dismiss', on_click=self.dismiss),
                        ]
                    ),
                    ft.Container(padding=ft.Padding.only(bottom=80)),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.Padding.only(left=10, top=15, bottom=100),
        )

    @log_errors
    async def create(self, e):
        """
        Create a registry.

        This method is called when a user wants to create a registry. It performs the following steps:
        1. Checks if a registry name is provided. If not, displays an error message and returns.
        2. Extracts necessary information from the embedded inception message.
        3. Constructs a group Habitat using the extracted information.
        4. Appends the ICP message to the agent's list of groups.

        Parameters:
        - _: Placeholder parameter, not used in the method.

        Returns:
        - None

        Raises:
        - None
        """
        rid = e.control.data
        if self.registry_name.value == '':
            self.registry_name.border_color = Colouring.get(Colouring.RED)
            await self.app.snack('Enter a name for the registry')
            self.update()
            return

        inits = {}

        oicp = serdering.SerderKERI(sad=self.embeds['icp'])

        inits['isith'] = oicp.ked['kt']
        inits['nsith'] = oicp.ked['nt']

        inits['estOnly'] = kering.TraitDex.EstOnly in oicp.ked['c']
        inits['DnD'] = kering.TraitDex.DoNotDelegate in oicp.ked['c']

        inits['toad'] = oicp.ked['bt']
        inits['wits'] = oicp.ked['b']
        inits['delpre'] = oicp.ked['di'] if 'di' in self.ked else None

        try:
            ghab = self.app.hby.makeGroupHab(
                group=self.group_alias.value,
                mhab=self.mhab,
                smids=self.signing_members,
                rmids=self.rotation_members,
                **inits,
            )
        except Exception as ex:
            await self.app.snack(f'Error joining group: {ex}')
            return

        self.app.agent.groups.append(dict(serder=oicp))
        self.app.agent.joining[ghab.pre] = rid

    async def dismiss(self, _):
        """
        Dismisses the notification and updates the page route.

        Args:
            _: Placeholder argument (ignored).

        Returns:
            None
        """
        await self.app.page.push_route('/notifications')
        self.app.page.update()
