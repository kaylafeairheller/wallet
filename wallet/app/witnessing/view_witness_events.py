"""
view_witness_events.py - View Witness Events Panel
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import flet as ft
import httpx
import pyperclip
from keri.core import coring

from wallet.app.witnessing.witness import WitnessBase
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


@dataclass
class WitnessEvent:
    """Simplified event model for wallet."""
    raw: str  # Raw JSON string
    data: dict[str, Any]  # Parsed event dict

    @property
    def type(self) -> str:
        """Event type: icp, rot, ixn, etc."""
        return self.data.get('t', 'unknown')

    @property
    def identifier(self) -> str:
        """AID (i field)."""
        return self.data.get('i', '')

    @property
    def sequence(self) -> int:
        """Decimal sequence number."""
        s = self.data.get('s', 0)
        if isinstance(s, int):
            return s
        try:
            return int(s, 16)
        except ValueError:
            return 0

    @property
    def sequence_hex(self) -> str:
        """Hex sequence number."""
        s = self.data.get('s', 0)
        if isinstance(s, int):
            return format(s, 'x')
        return str(s)

    @property
    def digest(self) -> str:
        """Event digest (d field)."""
        return self.data.get('d', '')

    @property
    def prior(self) -> str:
        """Prior event digest (p field)."""
        return self.data.get('p', '')

    @property
    def type_label(self) -> str:
        """Human-readable event type label."""
        labels = {
            'icp': 'Inception',
            'rot': 'Rotation',
            'ixn': 'Interaction',
            'dip': 'Delegated Inception',
            'drt': 'Delegated Rotation',
        }
        return labels.get(self.type, self.type.upper())


class EventListItem(ft.Container):
    """Single event in the list."""

    def __init__(self, event: WitnessEvent, on_click, selected: bool = False):
        # Event type color mapping
        type_colors = {
            'icp': ft.colors.GREEN,
            'rot': ft.colors.ORANGE,
            'ixn': ft.colors.BLUE,
            'dip': ft.colors.PURPLE,
            'drt': ft.colors.RED,
        }

        content = ft.Column([
            ft.Row([
                ft.Text(
                    f"s={event.sequence_hex} ({event.sequence})",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    font_family='monospace'
                ),
                ft.Container(
                    content=ft.Text(
                        event.type.upper(),
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.ON_PRIMARY
                    ),
                    bgcolor=type_colors.get(event.type, ft.colors.GREY),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=4)

        super().__init__(
            content=content,
            padding=10,
            border=ft.border.all(2 if selected else 1, ft.colors.PRIMARY if selected else ft.colors.OUTLINE),
            border_radius=8,
            bgcolor=ft.colors.SURFACE_VARIANT if selected else None,
            on_click=on_click,
            data=event
        )


class EventDetailPanel(ft.Column):
    """Event detail display panel."""

    def __init__(self, app, event: WitnessEvent):
        self.app = app
        self.event = event

        # Event type color
        type_colors = {
            'icp': ft.colors.GREEN,
            'rot': ft.colors.ORANGE,
            'ixn': ft.colors.BLUE,
            'dip': ft.colors.PURPLE,
            'drt': ft.colors.RED,
        }

        super().__init__([
            # Header
            ft.Row([
                ft.Text("Event Detail", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Text(
                        event.type_label,
                        size=12,
                        color=ft.colors.ON_PRIMARY
                    ),
                    bgcolor=type_colors.get(event.type, ft.colors.GREY),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Divider(opacity=0.1),

            # Metadata
            self._field_row("Identifier", event.identifier),
            self._field_row("Sequence", f"{event.sequence_hex} ({event.sequence})"),
            self._field_row("Digest", event.digest[:24] + "..." if len(event.digest) > 24 else event.digest),

            ft.Divider(opacity=0.1),

            # Raw JSON
            ft.Row([
                ft.Text("Raw Event", size=14, weight=ft.FontWeight.BOLD),
                ft.IconButton(
                    icon=ft.icons.COPY,
                    tooltip="Copy raw event",
                    on_click=self.copy_raw
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Container(
                content=ft.Text(
                    json.dumps(event.data, indent=2),
                    size=11,
                    font_family='monospace',
                    selectable=True
                ),
                bgcolor=ft.colors.SURFACE_VARIANT,
                padding=10,
                border_radius=8,
                expand=True
            )
        ], spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    def _field_row(self, label: str, value: str) -> ft.Row:
        """Create a labeled field row."""
        return ft.Row([
            ft.Text(f"{label}:", size=12, weight=ft.FontWeight.BOLD, width=80),
            ft.Text(value, size=12, font_family='monospace', selectable=True, expand=True)
        ])

    async def copy_raw(self, e):
        """Copy raw event to clipboard."""
        pyperclip.copy(json.dumps(self.event.data, indent=2))
        await self.app.snack('Event copied to clipboard!', duration=2000)


class ViewWitnessEvents(WitnessBase):
    """View events for a specific witness."""

    def __init__(self, app, witness):
        self.app = app
        self.witness = witness
        self.witness_prefix = witness['id']
        self.witness_alias = witness['alias']
        self.witness_oobi = witness['oobi']

        self.events: list[WitnessEvent] = []
        self.filtered_events: list[WitnessEvent] = []
        self.selected_event: WitnessEvent | None = None
        self.loading = False

        # Filter controls
        self.filter_type = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="all", label="All"),
                ft.Radio(value="icp", label="ICP"),
                ft.Radio(value="rot", label="ROT"),
                ft.Radio(value="ixn", label="IXN"),
            ], spacing=10, wrap=True),
            value="all",
            on_change=self.apply_filters
        )

        # Event list column
        self.event_list_column = ft.Column(
            [],
            spacing=4,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        # Event detail panel
        self.event_detail_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ARROW_BACK, size=48, color=ft.colors.ON_SURFACE_VARIANT),
                ft.Text("Select an event to view details", size=14, color=ft.colors.ON_SURFACE_VARIANT)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )

        # Loading indicator
        self.loading_indicator = ft.Container(
            content=ft.Column([
                ft.ProgressRing(),
                ft.Text("Loading events...", size=14)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            visible=False,
            expand=True
        )

        # Title row
        title_row = ft.Row([
            ft.Text(
                f"Events: {self.witness_alias}",
                size=20,
                weight=ft.FontWeight.BOLD
            ),
            ft.IconButton(
                icon=ft.icons.CLOSE,
                on_click=self.close
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Filter section
        filter_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.FILTER_LIST, size=16),
                    ft.Text("Filter by type:", size=12, weight=ft.FontWeight.BOLD)
                ], spacing=5),
                self.filter_type
            ], spacing=8),
            padding=ft.padding.only(left=10, bottom=10)
        )

        # Two-column layout
        content_row = ft.Row([
            # Left: Event list (40%)
            ft.Container(
                content=ft.Column([
                    ft.Text("Events", size=14, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.event_list_column,
                        expand=True
                    )
                ], spacing=8),
                expand=4,
                padding=10
            ),
            ft.VerticalDivider(width=1, opacity=0.2),
            # Right: Event detail (60%)
            ft.Container(
                content=ft.Stack([
                    self.event_detail_container,
                    self.loading_indicator
                ]),
                expand=6,
                padding=10
            )
        ], expand=True, spacing=0)

        # Main panel
        panel = ft.Container(
            content=ft.Column([
                filter_section,
                ft.Divider(opacity=0.1),
                content_row
            ], expand=True, spacing=0),
            expand=True,
            padding=ft.padding.only(left=10, top=10, right=10, bottom=100)
        )

        super().__init__(app, panel, title=title_row)

    def did_mount(self):
        """Load events when component mounts."""
        self.page.run_task(self.load_events)

    @log_errors
    async def load_events(self):
        """Fetch events from witness OOBI endpoint."""
        self.loading = True
        self.loading_indicator.visible = True
        self.update()

        try:
            logger.info(f'Fetching events from {self.witness_oobi}')

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.witness_oobi)
                response.raise_for_status()

                # Parse CESR stream
                data = response.content
                self.events = self._parse_cesr_events(data)

                logger.info(f'Loaded {len(self.events)} events')

                await self.apply_filters(None)

        except httpx.HTTPError as e:
            logger.exception(f'Error fetching events: {e}')
            await self.app.snack(f'Error loading events: {str(e)}', duration=5000)
            self.events = []
        finally:
            self.loading = False
            self.loading_indicator.visible = False
            self.update()

    def _parse_cesr_events(self, data: bytes) -> list[WitnessEvent]:
        """Parse CESR stream into events using keripy."""
        events = []

        try:
            # Use keripy's Serder to parse events
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
                    # Skip the serder size plus any attachments (simplified)
                    stream = stream[serder.size:]

                    # Skip attachments (rough heuristic - look for next event or end)
                    # This is simplified - proper parsing would handle all counter codes
                    while stream and stream[0:1] != b'{':
                        stream = stream[1:]

                except Exception as e:
                    logger.debug(f'Done parsing or error: {e}')
                    break

        except Exception as e:
            logger.exception(f'Error parsing CESR stream: {e}')

        return events

    @log_errors
    async def apply_filters(self, e):
        """Apply type filter to events."""
        filter_value = self.filter_type.value

        if filter_value == "all":
            self.filtered_events = self.events
        else:
            self.filtered_events = [ev for ev in self.events if ev.type == filter_value]

        await self.refresh_event_list()

    @log_errors
    async def refresh_event_list(self):
        """Rebuild event list UI."""
        self.event_list_column.controls.clear()

        if not self.filtered_events:
            self.event_list_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.INFO_OUTLINE, size=48, color=ft.colors.ON_SURFACE_VARIANT),
                        ft.Text("No events found", size=14, color=ft.colors.ON_SURFACE_VARIANT)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    expand=True
                )
            )
        else:
            for event in self.filtered_events:
                item = EventListItem(
                    event=event,
                    on_click=lambda e, ev=event: self.page.run_task(self.select_event, ev),
                    selected=(event == self.selected_event)
                )
                self.event_list_column.controls.append(item)

        self.update()

    @log_errors
    async def select_event(self, event: WitnessEvent):
        """Handle event selection."""
        self.selected_event = event
        self.event_detail_container.content = EventDetailPanel(self.app, event)
        await self.refresh_event_list()

    async def close(self, e):
        """Navigate back to witnesses list."""
        await self.app.page.push_route('/witnesses')
