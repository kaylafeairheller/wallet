"""
view_witness.py - View Witness Panel
"""

import datetime
import json
import logging

import flet as ft
import httpx
import pyperclip
from flet import Padding
from keri.app import connecting
from keri.core import coring

from wallet.app.witnessing.witness import WitnessBase
from wallet.app.witnessing.view_witness_events import WitnessEvent, EventListItem, EventDetailPanel
from wallet.logs import log_errors

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

        # Event-related state
        self.events: list[WitnessEvent] = []
        self.filtered_events: list[WitnessEvent] = []
        self.selected_event: WitnessEvent | None = None
        self.events_loaded = False

        # Create events section placeholder (will be populated after loading)
        self.events_section = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=16, height=16),
                ft.Text("Loading events...", size=12)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=10
        )

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
        witness_for_section: ft.Control
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
                    self.events_section,
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

    def did_mount(self):
        """Load events when component mounts."""
        self.page.run_task(self.load_events)

    @log_errors
    async def load_events(self):
        """Fetch events from witness OOBI endpoint."""
        try:
            logger.info(f'Fetching events from {self.witness["oobi"]}')

            # Use synchronous httpx in executor (old httpx version doesn't have AsyncClient)
            import asyncio
            loop = asyncio.get_event_loop()

            def fetch():
                response = httpx.get(self.witness['oobi'], timeout=30.0)
                return response.content

            data = await loop.run_in_executor(None, fetch)

            # Parse CESR stream
            self.events = self._parse_cesr_events(data)

            logger.info(f'Loaded {len(self.events)} events')

            self.filtered_events = self.events
            self.events_loaded = True
            await self.build_events_section()

        except Exception as e:
            logger.exception(f'Error fetching events: {e}')
            self.events_section.content = ft.Column([
                ft.Icon(ft.icons.ERROR_OUTLINE, size=32, color=ft.colors.ERROR),
                ft.Text(f'Error loading events: {str(e)}', size=12, color=ft.colors.ERROR)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
            self.update()

    def _parse_cesr_events(self, data: bytes) -> list[WitnessEvent]:
        """Parse CESR stream into events using keripy."""
        events = []

        try:
            stream = data
            while stream:
                try:
                    serder = coring.Serder(raw=stream)
                    event = WitnessEvent(
                        raw=serder.raw.decode('utf-8'),
                        data=serder.ked
                    )
                    events.append(event)

                    # Move past this event
                    stream = stream[serder.size:]

                    # Skip attachments (rough heuristic - look for next event or end)
                    while stream and stream[0:1] != b'{':
                        stream = stream[1:]

                except Exception:
                    break

        except Exception as e:
            logger.exception(f'Error parsing CESR stream: {e}')

        return events

    @log_errors
    async def build_events_section(self):
        """Build the events ExpansionTile with list and detail."""
        if not self.events:
            self.events_section.content = ft.Column([
                ft.Text('Events', weight=ft.FontWeight.BOLD, size=14),
                ft.Text('No events found', color=ft.colors.ON_SURFACE_VARIANT, italic=True, size=12)
            ])
            self.update()
            return

        # Event list column (scrollable)
        event_list_column = ft.Column(
            [
                EventListItem(
                    event=event,
                    on_click=lambda e, ev=event: self.page.run_task(self.select_event, ev),
                    selected=False
                )
                for event in self.filtered_events[:20]  # Limit to first 20 for performance
            ],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            height=300  # Fixed height for scrolling
        )

        # Event detail placeholder
        self.event_detail_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ARROW_BACK, size=32, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Text("Select an event to view details", size=12, color=ft.colors.ON_SURFACE_VARIANT)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            height=300,
            alignment=ft.alignment.center
        )

        # Build events ExpansionTile
        self.events_section.content = ft.ExpansionTile(
            title=ft.Text('Events', weight=ft.FontWeight.BOLD, size=14),
            subtitle=ft.Text(f'{len(self.events)} event{"s" if len(self.events) != 1 else ""}'),
            expanded=True,  # Expanded by default
            controls=[
                ft.Row([
                    # Left: Event list
                    ft.Container(
                        content=event_list_column,
                        expand=5
                    ),
                    ft.VerticalDivider(width=1, opacity=0.2),
                    # Right: Event detail
                    ft.Container(
                        content=self.event_detail_container,
                        expand=7
                    )
                ], spacing=10)
            ]
        )

        self.update()

    @log_errors
    async def select_event(self, event: WitnessEvent):
        """Handle event selection."""
        self.selected_event = event
        self.event_detail_container.content = EventDetailPanel(self.app, event)

        # Rebuild event list to update selection state
        if hasattr(self, 'events_section') and self.events_section.content:
            expansion_tile = self.events_section.content
            if hasattr(expansion_tile, 'controls') and expansion_tile.controls:
                row = expansion_tile.controls[0]
                if hasattr(row, 'controls'):
                    event_list_container = row.controls[0]
                    event_list_column = event_list_container.content

                    # Rebuild event list items with updated selection
                    event_list_column.controls = [
                        EventListItem(
                            event=ev,
                            on_click=lambda e, evt=ev: self.page.run_task(self.select_event, evt),
                            selected=(ev == self.selected_event)
                        )
                        for ev in self.filtered_events[:20]
                    ]

        self.update()

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
