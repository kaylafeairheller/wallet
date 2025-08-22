import logging
import base64
import io
import qrcode

import random
from urllib.parse import urljoin, urlparse

import flet as ft
from flet_core import FontWeight
from keri import kering

from wallet.app.colouring import Colouring
from wallet.app.contacting.contact import ContactBase
from wallet.app.oobing.oobi_resolver import OobiResolver

logger = logging.getLogger('wallet')


class ConnectWithContactPanel(ContactBase):
    """
    ConnectWithContactPanel class for creating a contact and connecting it to the given AID.
    """
        
    def __init__(self, app, hab):
        self.app = app
        self.hab = hab

        self.oobiTabs = ft.Column()
        self.oobi_qr = ft.Image(
            src='',
        )
        self.oobi_url = ft.Text('')
        self.oobi_copy = ft.IconButton()

        self.oobi_url = self.generate_oobi()

        self.verified = ft.Icon(ft.icons.SHIELD_OUTLINED, size=32, color=Colouring.get(Colouring.RED))
        super(ConnectWithContactPanel, self).__init__(app=app, panel=self.panel())

    async def callback(self, aid, alias):
        logger.info('callback: %s %s', aid, alias)
        route = f'/workflows/multisig/identifiers/{self.hab.pre}/contacts/{alias}/{aid}/challenge'
        print(route)
        self.app.page.route = route
        await self.app.page.update_async()

    async def error_callback(self, result):
        pass

    def load_oobis(self):
        oobis = []
        for wit in self.hab.kever.wits:
            urls = self.hab.fetchUrls(eid=wit, scheme=kering.Schemes.http) or self.hab.fetchUrls(
                eid=wit, scheme=kering.Schemes.https
            )
            if not urls:
                return []

            url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
            up = urlparse(url)
            oobis.append(urljoin(up.geturl(), f'/oobi/{self.hab.pre}/witness/{wit}'))

        return oobis
    
    def generate_oobi(self):
        oobis = self.load_oobis()

        if len(oobis) == 0:
            return ""

        oobi = random.choice(oobis)
        self.oobi = oobi
        img = qrcode.make(oobi)
        f = io.BytesIO()
        img.save(f)
        f.seek(0)

        async def copy(e):
            await self.app.page.set_clipboard_async(e.control.data)
            self.page.snack_bar = ft.SnackBar(ft.Text('OOBI URL Copied!'), duration=2000)

            self.page.snack_bar.open = True
            await self.page.update_async()

        self.oobi_qr = ft.Image(src_base64=base64.b64encode(f.read()).decode('utf-8'), width=175)
        self.oobi_url = ft.Container(
            content=ft.Text(
                value=oobi,
                tooltip=oobi,
                max_lines=3,
                size=12,
                overflow=ft.TextOverflow.VISIBLE,
                weight=ft.FontWeight.W_200,
                width=600,
            ),
            on_click=copy,
            data=oobi,
        )
        self.oobi_copy = ft.IconButton(icon=ft.icons.COPY_ROUNDED, data=oobi, on_click=copy, tooltip='Copy OOBI')

        self.oobiTabs.controls.clear()
        self.oobiTabs.controls.append(
            ft.Column(
                [
                    ft.Row([self.oobi_url, self.oobi_copy]),
                    ft.Row([self.oobi_qr]),
                    ft.Container(padding=ft.padding.only(top=6)),
                ]
            )
        )

        return oobi
    
    def panel(self):
        orr = OobiResolver(self.app, self.callback, self.error_callback)
        return ft.Container(
            content=ft.Column([
                ft.Text('Connect with Contact', size=24), 
                orr.render(),
                ft.Container(
                    content=ft.Column([
                    ft.Text(
                        'Your Identifier',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Text(
                        f'{self.hab.name} | {self.hab.pre}',
                    ),
                    ft.Container(
                        content=self.oobiTabs,
                    ),
                ]),
                ),
            ]),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=ft.padding.only(left=10, top=15),
        )