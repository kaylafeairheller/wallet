"""
view_witness.py - View Witness Panel
"""

import datetime
import logging

import flet as ft
import pyperclip
from flet import Padding
from keri.app import connecting

from wallet.app.witnessing.witness import WitnessBase

logger = logging.getLogger('wallet')


class ViewWitness(WitnessBase):
    def __init__(self, app, witness):
        self.app = app
        self.witness = witness
        self.pre = witness['id']
        self.kever = self.app.agent.hby.kevers[self.pre]
        self.cancelled = False

        self.alias = self.witness['alias']

        logger.info(f'Loading witness for {self.alias}')

        sn, dt = self.get_sn_date()
        self.sn_text = ft.Text(sn)
        self.dt_text = ft.Text(dt.strftime('%Y-%m-%d %I:%M %p'))

        super(ViewWitness, self).__init__(
            app=app,
            panel=self.panel(),
            title=ft.Row(
                controls=[
                    ft.Container(
                        ft.Text(value=f'Alias: {self.alias}', size=24),
                        padding=ft.Padding.only(left=10, top=0, right=10, bottom=0),
                    ),
                    ft.Container(
                        ft.IconButton(icon=ft.Icons.CLOSE, on_click=self.close),
                        alignment=ft.Alignment.TOP_RIGHT,
                        expand=True,
                        padding=ft.Padding.only(left=0, top=0, right=10, bottom=0),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def get_sn_date(self):
        org = connecting.Organizer(hby=self.app.agent.hby)
        witness = org.get(self.witness['id'])
        dt = None
        if 'last-refresh' in witness:
            dt = datetime.datetime.fromisoformat(witness['last-refresh'])
        elif self.kever and self.kever.dater:
            dt = datetime.datetime.fromisoformat(f'{self.kever.dater.dts}')
        sn = None
        if self.kever and self.kever.sner:
            sn = self.kever.sn

        return sn, dt

    def panel(self):
        # Find identifiers that use this witness
        using_habs = []
        for hab in self.app.hby.habs.values():
            if self.pre in hab.kever.wits:
                using_habs.append(hab)

        # Sort alphabetically
        using_habs = sorted(using_habs, key=lambda h: h.name.lower())

        # Build the "Witness for" section as collapsible
        if using_habs:
            witness_for_section = ft.ExpansionTile(
                title=ft.Text('Witness for', weight=ft.FontWeight.BOLD, size=14),
                subtitle=ft.Text(f'{len(using_habs)} identifier{"s" if len(using_habs) != 1 else ""}'),
                expanded=len(using_habs) <= 3,
                controls=[
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON),
                        title=ft.Text(hab.name),
                        subtitle=ft.Text(hab.pre, font_family='monospace', size=12),
                        on_click=self.view_identifier,
                        data=hab.pre,
                    )
                    for hab in using_habs
                ],
            )
        else:
            witness_for_section = ft.Container(
                content=ft.Column(
                    [
                        ft.Text('Witness for:', weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(
                            'Not currently witnessing any identifiers',
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            italic=True,
                        ),
                    ]
                ),
            )

        return ft.Container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text('Prefix:', weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(self.witness['id'], font_family='monospace'),
                        ]
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Text('OOBI:', weight=ft.FontWeight.BOLD, size=14),
                                        ft.Text(
                                            value=f'{self.witness["oobi"]}',
                                            tooltip='OOBI URL',
                                            max_lines=3,
                                            overflow=ft.TextOverflow.VISIBLE,
                                            size=14,
                                            weight=ft.FontWeight.W_200,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.COPY_ROUNDED,
                                            data=self.witness['oobi'],
                                            on_click=self.copy_oobi,
                                            padding=Padding.only(right=10),
                                        ),
                                    ]
                                )
                            ]
                        )
                    ),
                    ft.Divider(),
                    witness_for_section,
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.Button(
                                'Close',
                                on_click=self.close,
                                data=self.app,
                            )
                        ]
                    ),
                ]
            ),
            expand=True,
            alignment=ft.Alignment.TOP_LEFT,
            padding=Padding.only(left=10, top=15, bottom=100),
        )

    async def close(self, e):
        self.cancelled = True
        await self.app.page.push_route('/witnesses')
        self.app.page.update()

    async def view_identifier(self, e):
        """Navigate to view the selected identifier."""
        prefix = e.control.data
        await self.app.page.push_route(f'/identifiers/{prefix}/view')

    async def copy_oobi(self, e):
        pyperclip.copy(e.control.data)
        await self.app.snack('OOBI URL Copied!', duration=2000)

    async def select_identifier(self, e):
        self.selected_identifier = e.control.value
        self.update()

    async def show_verify(self):
        return self.selected_identifier is not None
