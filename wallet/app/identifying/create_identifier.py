"""
create_identifier.py - Panel for creating a new identifier
"""

import logging

import flet as ft
from flet_core import FontWeight, padding
from keri.app import connecting, grouping
from keri.core import coring, signing
from  ordered_set import OrderedSet as oset

from wallet.app.identifying.identifier import IdentifierBase
from wallet.core.configing import Environments
from wallet.logs import log_errors

logger = logging.getLogger('wallet')


class CreateIdentifierPanel(IdentifierBase):
    """
    CreateIdentifierPanel class for creating a new identifier in the application.
    """

    def __init__(self, app):
        self.app = app
        self.org = connecting.Organizer(hby=app.agent.hby)
        self.alias = ft.TextField(
            label='Alias',
            hint_text='Local alias for identifier',
        )
        self.eo = ft.Checkbox(
            label='Establishment Only',
            value=False,
        )
        self.dnd = ft.Checkbox(
            label='Do Not Delegate',
            value=False,
        )

        salt = coring.randomNonce()[2:23]
        self.salt = ft.TextField(
            label='Key Salt',
            value=salt,
            password=True,
            can_reveal_password=True,
            width=300,
        )
        self.keyCount = ft.TextField(
            label='Signing',
            width=100,
            value='1',
        )
        self.nkeyCount = ft.TextField(
            label='Rotation',
            width=100,
            value='1',
        )
        self.keySith = ft.TextField(
            label='Signing Threshold',
            width=225,
            value='1',
        )
        self.nkeySith = ft.TextField(
            label='Rotation Threshold',
            width=225,
            value='1',
        )
        self.toad = ft.TextField(
            value='0',
        )

        self.signingList = ft.Column(width=550)
        self.signingDropdown = ft.Dropdown(
            options=[],
            width=420,
            text_size=12,
            height=55,
        )
        self.rotationList = ft.Column(width=550)
        self.rotationDropdown = ft.Dropdown(
            options=[],
            width=420,
            text_size=12,
            height=55,
            # border_color=ft.colors.with_opacity(0.25, ft.colors.GREY),
            disabled=True,
            text_style=ft.TextStyle(font_family='monospace'),
        )
        self.rotationAddButton = ft.IconButton(
            icon=ft.icons.ADD,
            tooltip='Add Member',
            on_click=self.add_rotation,
            disabled=True,
        )
        self.rotSith = ft.TextField(
            label='Rotation Threshold',
            width=225,
            value='1',
            disabled=True,
        )

        async def resalt(_):
            self.salt.value = coring.randomNonce()[2:23]
            await self.salt.update_async()

        self.salty = ft.Column(
            [
                ft.Row(
                    [
                        self.salt,
                        ft.IconButton(
                            icon=ft.icons.CHANGE_CIRCLE_OUTLINED,
                            on_click=resalt,
                        ),
                    ]
                ),
                ft.Text('Number of Keys / Threshold', weight=FontWeight.BOLD),
                ft.Row([self.keyCount, self.keySith]),
                ft.Row([self.nkeyCount, self.nkeySith]),
            ],
        )

        self.randy = ft.Column(
            [
                ft.Text('Number of Keys / Threshold', weight=FontWeight.BOLD),
                ft.Row([self.keyCount, self.keySith]),
                ft.Row([self.nkeyCount, self.nkeySith]),
            ],
        )

        self.group = ft.Column(
            [
                ft.Text('Signing members'),
                self.signingList,
                ft.Row(
                    [
                        self.signingDropdown,
                        ft.IconButton(
                            icon=ft.icons.ADD,
                            tooltip='Add Member',
                            on_click=self.addMember,
                        ),
                    ]
                ),
                ft.Container(padding=ft.padding.only(top=8)),
                ft.Row([self.keySith]),
                ft.Container(padding=ft.padding.only(top=20)),
                ft.Checkbox(
                    label='Rotation Members (if different from signing)',
                    value=False,
                    on_change=self.enableRotationMembers,
                ),
                self.rotationList,
                ft.Row([self.rotationDropdown, self.rotationAddButton]),
                ft.Container(padding=ft.padding.only(top=8)),
                ft.Row([self.rotSith]),
            ],
        )

        self.witnesses = self.loadWitnesses(app)
        self.witness_pools = self.loadWitnessPools(app)

        self.keyTypePanel = ft.Container(content=self.salty, padding=padding.only(left=50))
        self.keyType = 'salty'

        self.witnessList = ft.Column(width=575)
        self.witnessDropdown = ft.Dropdown(
            options=self.witnesses,
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
        )
        self.witnessPoolDropdown = ft.Dropdown(
            options=self.witness_pools,
            width=420,
            text_size=14,
            visible=False if self.app.environment is Environments.PRODUCTION else True,
        )

        self.delegatorDropdown = ft.Dropdown(
            options=self.witnesses,
            width=420,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
        )
        self.members = self.loadMembers(app)
        self.signingDropdown.options = self.members
        self.rotationDropdown.options = list(self.members)

        self.useWitnessPoolCheckbox = ft.Checkbox(
            label='Use Pool',
            value=False,
            on_change=self.on_use_pool_change,
            visible=False if self.app.environment in [Environments.PRODUCTION, Environments.DEVELOPMENT] else True,
        )

        self.witnessSelectorRow = ft.Row(
            controls=[
                self.witnessDropdown,
                ft.IconButton(
                    icon=ft.icons.ADD,
                    tooltip='Add Witness',
                    on_click=self.addWitness,
                ),
            ],
            visible=False if self.app.environment is Environments.PRODUCTION else True,
        )
        self.witnessPoolRadioRow = ft.Row(
            controls=[
                ft.RadioGroup(
                    content=ft.Column([*[ft.Radio(value=pool, label=pool) for pool in self.app.wit_pools.keys()]]),
                    on_change=self.on_pool_radio_change,
                )
            ],
            visible=True if self.app.environment is Environments.PRODUCTION else False,
        )
        self.panel_ref = self.panel()

        super(CreateIdentifierPanel, self).__init__(app, self.panel_ref)

    async def keyTypeChanged(self, e):
        self.keyType = e.control.value
        match e.control.value:
            case 'salty':
                self.keyTypePanel.content = self.salty
            case 'randy':
                self.keyTypePanel.content = self.randy
            case 'group':
                self.keyTypePanel.content = self.group
        await self.update_async()

    def witnessTile(self, wit_ct, on_delete):
        """
        Parameters:
            wit_ct (dict): contact entry of the witness
        """
        if 'alias' in wit_ct:
            title = ft.Column([ft.Text(wit_ct['alias']), ft.Text(wit_ct['id'], font_family='monospace')])
        else:
            title = ft.Text(wit_ct['id'], font_family='monospace')
        return ft.ListTile(
            title=title,
            trailing=ft.IconButton(
                ft.icons.DELETE_OUTLINED,
                on_click=on_delete,
                data=wit_ct['id'],
            ),
            data=wit_ct['id'],
        )

    async def addWitness(self, _):
        if not self.witnessDropdown.value:
            await self.app.snack('Please select a witness')
            return
        witness = self.witnessDropdown.value
        self.witnessDropdown.value = None

        if self.findSelectedWitness(witness) is not None:
            await self.app.snack(f'You can not add {witness} more than once')
            return

        witness = self.org.get(witness)
        self.witnessList.controls.append(self.witnessTile(witness, self.deleteWitness))

        self.toad.value = str(self.recommendedThold(len(self.witnessList.controls)))
        await self.toad.update_async()

        await self.witnessDropdown.update_async()
        await self.witnessList.update_async()

    async def deleteWitness(self, e):
        aid = e.control.data
        if (tile := self.findSelectedWitness(aid)) is not None:
            self.witnessList.controls.remove(tile)

        self.toad.value = str(self.recommendedThold(len(self.witnessList.controls)))
        await self.toad.update_async()
        await self.witnessList.update_async()

    def findSelectedWitness(self, aid):
        for tile in self.witnessList.controls:
            if tile.data == aid:
                return tile

        return None

    async def addMember(self, _):
        if self.signingDropdown.value is None:
            return

        idx = int(self.signingDropdown.value)
        m = self.app.members[idx]
        self.signingList.controls.append(
            ft.ListTile(
                title=ft.Text(f'{m["alias"]}', size=14),
                subtitle=ft.Text(f'({m["id"]})', font_family='monospace', size=10),
                trailing=ft.IconButton(
                    ft.icons.DELETE_OUTLINED,
                    on_click=self.deleteMember,
                    data=self.signingDropdown.value,
                ),
                data=self.signingDropdown.value,
            ),
        )

        for option in self.signingDropdown.options:
            if option.key == self.signingDropdown.value:
                self.signingDropdown.options.remove(option)

        self.signingDropdown.value = None
        await self.signingDropdown.update_async()
        await self.signingList.update_async()

    async def enableRotationMembers(self, e):
        self.rotationDropdown.disabled = not e.control.value
        self.rotSith.disabled = not e.control.value
        self.rotationAddButton.disabled = not e.control.value
        self.rotationList.controls.clear()

        await self.rotationList.update_async()
        await self.rotationDropdown.update_async()
        await self.rotSith.update_async()
        await self.rotationAddButton.update_async()

    async def add_rotation(self, _):
        if self.rotationDropdown.value is None:
            return

        idx = int(self.rotationDropdown.value)
        m = self.app.members[idx]
        self.rotationList.controls.append(
            ft.ListTile(
                title=ft.Text(f'{m["alias"]}', size=14),
                subtitle=ft.Text(f'({m["id"]})', font_family='monospace', size=10),
                trailing=ft.IconButton(
                    ft.icons.DELETE_OUTLINED,
                    on_click=self.deleteRotation,
                    data=self.rotationDropdown.value,
                ),
                data=self.rotationDropdown.value,
            ),
        )

        for option in self.rotationDropdown.options:
            if option.key == self.rotationDropdown.value:
                self.rotationDropdown.options.remove(option)

        self.rotationDropdown.value = None
        await self.rotationDropdown.update_async()
        await self.rotationList.update_async()

    async def deleteMember(self, e):
        aid = e.control.data
        for tile in self.signingList.controls:
            if tile.data == aid:
                self.signingList.controls.remove(tile)
                self.signingDropdown.options.append(ft.dropdown.Option(aid))
                break

        self.toad.value = str(self.recommendedThold(len(self.signingList.controls)))
        await self.toad.update_async()
        await self.signingDropdown.update_async()
        await self.signingList.update_async()

    async def deleteRotation(self, e):
        aid = e.control.data
        for tile in self.rotationList.controls:
            if tile.data == aid:
                self.rotationList.controls.remove(tile)
                self.rotationDropdown.options.append(ft.dropdown.Option(aid))
                break

        self.toad.value = str(self.recommendedThold(len(self.rotationList.controls)))
        await self.toad.update_async()
        await self.rotationDropdown.update_async()
        await self.rotationList.update_async()

    @log_errors
    async def createAid(self, _):
        if self.alias.value == '':
            await self.app.snack('Alias is required')
            return
        
        self.hab = self.app.hby.habByName(name='harry')

        kwargs = dict(algo=self.keyType)
        if self.keyType == 'salty':
            if self.salt.value is None or len(self.salt.value) != 21:
                await self.app.snack('Salt is required and must be 21 characters long')
                return

            kwargs['salt'] = signing.Salter(raw=self.salt.value.encode('utf-8')).qb64
            kwargs['icount'] = int(self.keyCount.value)
            kwargs['isith'] = int(self.keySith.value)
            kwargs['ncount'] = int(self.nkeyCount.value)
            kwargs['nsith'] = int(self.nkeySith.value)

        elif self.keyType == 'randy':
            kwargs['salt'] = None
            kwargs['icount'] = int(self.keyCount.value)
            kwargs['isith'] = int(self.keySith.value)
            kwargs['ncount'] = int(self.nkeyCount.value)
            kwargs['nsith'] = int(self.nkeySith.value)

        elif self.keyType == 'group':
            kwargs['isith'] = int(self.keySith.value)
            kwargs['nsith'] = int(self.nkeySith.value)

            smids = []
            for tile in self.signingList.controls:
                m = self.app.members[int(tile.data)]
                smids.append(m['id'])

            if not self.rotSith.disabled:
                rmids = []
                for tile in self.rotationList.controls:
                    m = self.app.members[int(tile.data)]
                    rmids.append(m['id'])
            else:
                rmids = smids

            smids.append(self.hab.pre)

            kwargs['smids'] = smids
            kwargs['rmids'] = rmids

        # TODO - Add delegator support here
        delpre = self.delegatorDropdown.value

        kwargs['wits'] = [c.data for c in self.witnessList.controls]
        kwargs['toad'] = self.toad.value
        kwargs['estOnly'] = self.eo.value
        kwargs['DnD'] = self.dnd.value
        if delpre:
            kwargs['delpre'] = self.delegatorDropdown.value

        if self.keyType == 'group':
            print(kwargs)
            del kwargs["algo"]
            ghab = self.app.hby.makeGroupHab(group=self.alias.value, mhab=self.hab, **kwargs)

            icp = ghab.makeOwnInception(allowPartiallySigned=True)

            # Create a notification EXN message to send to the other agents
            exn, ims = grouping.multisigInceptExn(ghab.mhab,
                                                    smids=ghab.smids,
                                                    rmids=ghab.rmids,
                                                    icp=icp)
            others = list(oset(smids))

            others.remove(ghab.mhab.pre)

            for recpt in others:  # this goes to other participants only as a signaling mechanism
                self.app.agent.postman.send(src=ghab.mhab.pre,
                                    dest=recpt,
                                    topic="multisig",
                                    serder=exn,
                                    attachment=ims)

            print(f"Group identifier inception initialized for {ghab.pre}")
            prefixer = coring.Prefixer(qb64=ghab.pre)
            seqner = coring.Seqner(sn=0)
            saider = coring.Saider(qb64=prefixer.qb64)
            self.app.agent.counselor.start(prefixer=prefixer, seqner=seqner, saider=saider,
                                    ghab=ghab)


            await self.app.snack(f'Creating {ghab.pre}, waiting for multisig collaboration...')
        else:
            hab = self.app.hby.makeHab(name=self.alias.value, **kwargs)
            serder, _, _ = hab.getOwnEvent(sn=0)

            if delpre:
                self.app.agent.anchors.push(dict(sn=0))
                await self.app.snack(f'Creating {hab.pre}, waiting for delegation approval...')

            elif len(kwargs['wits']) > 0:
                self.app.agent.witners.push(dict(serder=serder))
                await self.app.snack(f'Creating {hab.pre}, waiting for witness receipts...')

            else:
                await self.app.snack(f'Created AID {hab.pre}.')

        self.reset()
        self.app.page.route = '/identifiers'
        await self.page.update_async()

    @staticmethod
    def loadWitnesses(app):
        return [
            ft.dropdown.Option(
                key=wit['id'],
                text=f'{wit["alias"]} | {wit["id"]}' if wit['alias'] else f'{wit["id"]}',
                data=(wit['id'], wit['alias']),
            )
            for wit in app.witnesses
        ]

    @staticmethod
    def loadWitnessPools(app):
        return [ft.dropdown.Option(pool) for pool in app.wit_pools.keys()]

    @staticmethod
    def loadMembers(app):
        return [ft.dropdown.Option(key=idx, text=f'{m["alias"]}') for idx, m in enumerate(app.members)]

    async def cancel(self, _):
        self.reset()
        self.app.page.route = '/identifiers'
        await self.page.update_async()

    def reset(self):
        self.alias.value = ''
        self.eo.value = False
        self.dnd.value = False
        self.keyTypePanel = ft.Container(content=self.salty, padding=padding.only(left=50))
        self.keyType = 'salty'
        self.nkeySith.value = '1'
        self.keySith.value = '1'
        self.nkeyCount.value = '1'
        self.keyCount.value = '1'
        self.salt.value = coring.randomNonce()[2:23]

    @staticmethod
    def recommendedThold(numWits):
        match numWits:
            case 0:
                return 0
            case 1:
                return 1
            case 2 | 3:
                return 2
            case 4:
                return 3
            case 5 | 6:
                return 4
            case 7:
                return 5
            case 8 | 9:
                return 7
            case 10:
                return 8

    async def addWitnessesFromPoolDropdown(self, _):
        if not self.witnessPoolDropdown.value:
            return
        pool = self.witnessPoolDropdown.value
        await self.addWitnessesFromPool(pool)
        await self.witnessPoolDropdown.update_async()

    async def addWitnessesFromPoolRadioButton(self, e):
        pool = e.control.value
        if not pool:
            return
        self.witnessList.controls.clear()
        await self.addWitnessesFromPool(pool)

    async def addWitnessesFromPool(self, pool):
        """Loads all witnesses from a pool idempotently and adjusts threshold appropriately."""
        pool = self.app.wit_pools[pool]
        logger.info(f'using witnesses: {pool}')

        for wit_pre in pool:  # Force to only be in pool once
            if wit_pre in [ctl.data for ctl in self.witnessList.controls]:
                continue
            else:
                contact = self.org.get(wit_pre)
                witness = contact if contact else {'id': wit_pre}
                self.witnessList.controls.append(self.witnessTile(witness, self.deleteWitness))
        self.witnessPoolDropdown.value = None

        self.toad.value = str(self.recommendedThold(len(self.witnessList.controls)))
        await self.toad.update_async()
        await self.witnessList.update_async()

    @log_errors
    async def on_use_pool_change(self, e):
        use_pool = e.control.value
        if use_pool:
            logger.info(f'Use witness pool {self.app.wit_pools}')
            self.witnessSelectorRow.controls.clear()
            self.witnessSelectorRow.controls.append(self.witnessPoolDropdown)
            self.witnessSelectorRow.controls.append(
                ft.IconButton(icon=ft.icons.ADD, tooltip='Add Witnesses in Pool', on_click=self.addWitnessesFromPoolDropdown)
            )
        else:
            logger.info(f'Use witness list {self.app.witnesses}')
            self.witnessSelectorRow.controls.clear()
            self.witnessSelectorRow.controls.append(self.witnessDropdown)
            self.witnessSelectorRow.controls.append(
                ft.IconButton(icon=ft.icons.ADD, tooltip='Add Witnesses', on_click=self.addWitness)
            )
        await self.page.update_async()

    @log_errors
    async def on_pool_radio_change(self, e):
        await self.addWitnessesFromPoolRadioButton(e)

    def panel(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Create Identifier',
                        weight=FontWeight.BOLD,
                    ),
                    ft.Row(
                        [
                            self.alias,
                        ]
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        'Witnesses',
                                        weight=FontWeight.BOLD,
                                    ),
                                    self.useWitnessPoolCheckbox,
                                ]
                            ),
                            self.witnessList,
                            self.witnessSelectorRow,
                            self.witnessPoolRadioRow,
                        ]
                    ),
                    ft.ExpansionTile(
                        title=ft.Text('Advanced Configuration'),
                        affinity=ft.TileAffinity.LEADING,
                        initially_expanded=False,
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Container(padding=padding.only(top=10)),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                'Key Type',
                                                weight=FontWeight.BOLD,
                                            ),
                                            ft.RadioGroup(
                                                content=ft.Row(
                                                    [
                                                        ft.Radio(
                                                            value='salty',
                                                            label='Key Chain',
                                                        ),
                                                        ft.Radio(
                                                            value='randy',
                                                            label='Random Key',
                                                        ),
                                                        # ft.Radio(
                                                        #     value='group',
                                                        #     label='Group Multisig',
                                                        # ),
                                                    ]
                                                ),
                                                value='salty',
                                                on_change=self.keyTypeChanged,
                                            ),
                                        ]
                                    ),
                                    self.keyTypePanel,
                                    ft.Row(
                                        [
                                            ft.Column([self.eo]),
                                            ft.Column([self.dnd]),
                                        ]
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                'Delegator',
                                                weight=FontWeight.BOLD,
                                            ),
                                            ft.Row(
                                                [
                                                    self.delegatorDropdown,
                                                ]
                                            ),
                                        ]
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                'Threshold of Acceptable Duplicity',
                                                weight=FontWeight.BOLD,
                                            ),
                                            self.toad,
                                        ]
                                    ),
                                ]
                            ),
                        ],
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                'Create',
                                on_click=self.createAid,
                            ),
                            ft.ElevatedButton(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=padding.only(bottom=105),
        )
