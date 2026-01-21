import datetime
import logging
import urllib.parse
from urllib.parse import urlparse

import flet as ft
from flet import Padding
from keri.app import connecting

from wallet.app.contacting.contact import ContactBase

logger = logging.getLogger('wallet')


class Contacts(ContactBase):
    def __init__(self, app):
        self.app = app
        self.list = ft.Column([], spacing=0, expand=True)

        super().__init__(app, ft.Container(content=self.list, padding=Padding.only(bottom=125)))

    def did_mount(self):
        self.page.run_task(self.refresh_contacts)

    async def refresh_contacts(self):
        org = connecting.Organizer(hby=self.app.agent.hby)
        await self.set_contacts(org.list())
        self.page.update()

    async def add_contact(self, _):
        await self.app.page.push_route('/contacts/create')
        self.app.page.update()

    async def set_contacts(self, contacts):
        self.list.controls.clear()
        icon = ft.Icons.PERSON
        tip = 'Contacts'

        contacts = sorted(contacts, key=lambda c: c.get('alias', c['id']).lower())
        contacts = list(filter(lambda c: 'tag=witness' not in c['oobi'], contacts))

        if len(contacts) == 0:
            self.list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=64, color=ft.Colors.ON_SURFACE_VARIANT),
                            ft.Text('No contacts yet', size=18, weight=ft.FontWeight.W_500),
                            ft.Text('Contacts you add will appear here', size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=ft.Padding.all(40),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                )
            )
        else:
            for contact in contacts:
                pre = contact['id']
                kever = self.app.agent.hby.kevers[pre]
                c = urllib.parse.parse_qs(urlparse(contact['oobi']).query)
                if 'tag' in c and 'witness' in c['tag']:
                    continue

                view = ft.PopupMenuItem(
                    content=ft.Text('View'),
                    icon=ft.Icons.PAGEVIEW,
                    on_click=self.view_contact,
                )
                view.data = contact

                dt = None
                if 'last-refresh' in contact:
                    dt = datetime.datetime.fromisoformat(contact['last-refresh'])
                elif kever and kever.dater:
                    dt = datetime.datetime.fromisoformat(f'{kever.dater.dts}')
                sn = None
                if kever and kever.sner:
                    sn = kever.sn

                title = ft.Text(contact['alias'])
                if dt is not None and sn is not None:
                    title = ft.Text(f'{contact["alias"]} (SN: {sn} Datetime: {dt.strftime("%Y-%m-%d %I:%M %p")})')

                tile = ft.ListTile(
                    leading=ft.Icon(icon, tooltip=tip),
                    title=title,
                    subtitle=ft.Text(contact['id'], font_family='monospace'),
                    trailing=ft.PopupMenuButton(
                        tooltip=None,
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            view,
                            ft.PopupMenuItem(content=ft.Text('Delete'), icon=ft.Icons.DELETE_FOREVER),
                        ],
                    ),
                    on_click=self.view_contact,
                    data=contact,
                    shape=ft.StadiumBorder(),
                )
                self.list.controls.append(ft.Container(content=tile))
                self.list.controls.append(ft.Divider(opacity=0.1))

        self.update()

    async def view_contact(self, e):
        contact = e.control.data
        await self.app.page.push_route(f'/contacts/{contact["id"]}/view')
