"""
Credentials module for the Wallet application.
"""

import logging

import flet as ft

from wallet.app import colouring
from wallet.app.credentialing.credential import CredentialBase
from wallet.app.identifying.identifiers import Identifiers
from wallet.logs import log_errors

logger = logging.getLogger('wallet')

class Credentials(CredentialBase):
    """
    Class representing credentials in the application.

    Attributes:
        page (ft.Page): The page object associated with the app.
        list (ft.Column): The column object representing the list of credentials.
    """

    def __init__(self, app):
        self.app = app
        self.page: ft.Page = app.page
        self.list = ft.Column([], spacing=0, expand=True)

        super().__init__(app, ft.Container(content=self.list, padding=ft.padding.only(bottom=125)))

    def did_mount(self):
        self.page.run_task(self.refresh_credentials)

    async def refresh_credentials(self):
        """
        Refreshes the credentials by setting them to the current list.
        """
        await self.set_credentials()
        self.update()

    @log_errors
    async def set_credentials(self):
        """
        Sets the credentials for the list view.
        """
        self.list.controls.clear()

        # habs = self.app.agent.hby.habs.values()
        
        # hab = self.app.agent.hby.habs[prefix]

        # if len(habs) == 0:
        #     self.list.controls.append(
        #         ft.Container(
        #             content=ft.Text(
        #                 'No credentials found.',
        #             ),
        #             padding=ft.padding.all(20),
        #         )
        #     )
        # else:
            # for hab in habs:

        # habs = Identifiers.get_habs(self.app.agent)
        for pre in self.app.agent.hby.habs:
            hab = self.app.agent.hby.habByPre(pre)
            print(hab)
            
            saids = self.app.agent.rgy.reger.subjs.get(keys=hab.pre)
            print(saids)
            print(hab.db)
            # creds = self.app.agent.rgy.reger.cloneCreds(saids, hab.db)

            for s in saids:
                tip = 'Credential'
                icon = ft.icons.LOCK_OUTLINED

                print(s)

                # saids = self.app.agent.rgy.reger.issus.get(keys=hab.pre)
                # scads = self.app.agent.rgy.reger.schms.get(keys=self.schema)
                # saids = [saider for saider in saids if saider.qb64 in [saider.qb64 for saider in scads]]

                # for said in saids:
                #     print(said)

                view = ft.PopupMenuItem(text='View', icon=ft.icons.PAGEVIEW, on_click=self.view_credential)
                view.data = hab
                rotate = ft.PopupMenuItem(
                    text='Rotate',
                    icon=ft.icons.ROTATE_RIGHT,
                    on_click=print('rotate!'),
                )
                rotate.data = hab
                delete = ft.PopupMenuItem(
                    text='Delete',
                    icon=ft.icons.DELETE_FOREVER,
                    on_click=print('delete!'),
                )
                delete.data = hab

                title_row = ft.Row(
                    [
                        ft.Text(
                            hab.pre,
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
                        value=hab.name,
                        color=colouring.Colouring.get(colouring.Colouring.ON_SURFACE),
                    ),
                    subtitle=title_row,
                    trailing=ft.PopupMenuButton(
                        tooltip=None,
                        icon=ft.icons.MORE_VERT,
                        items=[
                            view,
                            rotate,
                            delete,
                        ],
                    ),
                    on_click=self.view_credential,
                    data=hab,
                    shape=ft.StadiumBorder(),
                )
                self.list.controls.append(
                    ft.Container(
                        content=tile,
                    )
                )
                self.list.controls.append(ft.Divider(opacity=0.1))

        await self.update_async()

    async def view_credential(self, e):
        """
        View the credential details.

        Args:
            e: The event object containing the identifier data.

        Returns:
            None
        """
        hab = e.control.data
        self.app.page.route = f'/credentials/{hab.pre}/view'
        await self.app.page.update_async()
