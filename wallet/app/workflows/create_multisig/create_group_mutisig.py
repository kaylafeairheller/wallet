import logging
import json

import flet as ft
from flet_core import FontWeight
from keri.core import coring, signing
from keri.app import connecting, grouping

from  ordered_set import OrderedSet as oset
from wallet.logs import log_errors
from wallet.app.identifying.identifier import IdentifierBase

logger = logging.getLogger('wallet')


class CreateMultisigIdentifierPanel(IdentifierBase):
    """
    CreateMutisigPanel class for creating a Group Multisig with two given identifiers.
    """
        
    def __init__(self, app):
        self.app = app
        self.org = connecting.Organizer(hby=app.agent.hby)

        print("WITNESSES", app.witnesses)

        org = connecting.Organizer(hby=app.agent.hby)
        print("CONTACTS", org.list())
        # self.hab = hab
        # self.postman = forwarding.Poster(hby=self.app.hby)
        # self.counselor = grouping.Counselor(hby=self.app.hby)

        self.identifiersDropdown = ft.Dropdown(
            options=self.loadIdentifiers(app),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
        )

        self.contactsDropdown = ft.Dropdown(
            options=self.loadContacts(app),
            width=550,
            text_size=14,
            text_style=ft.TextStyle(font_family='monospace'),
        )
        
        # self.contact = f'{alias} | {aid}'

        # print("ALIAS IS HERE", self.alias)

        # cts = self.org.find('alias', self.alias)
        # if len(cts) > 1:
        #     logger.error(f'OOBI resolve failed: multiple contacts found for alias {self.alias}')
        #     return False
        # self.aid = cts[0]['id']
        
        # self.contact = f'{self.alias} | {self.aid}'

        self.multisig_alias = ft.TextField(
            label='Alias',
            hint_text='Local alias for Group Multisig',
        )

        self.order = ["yours", "theirs"]  # Default order
        self.lead = ft.Column()
        self.recipient = ft.Column() 

        # Loading default witnesses
        self.witnessList = self.loadWitnesses(app)

        self.keySith = ft.TextField(
            label='Signing Threshold',
            width=225,
            value='2',
        )
        self.nkeySith = ft.TextField(
            label='Rotation Threshold',
            width=225,
            value='2',
        )

        # self.smids = [hab.pre, aid]

        super().__init__(app=app, panel=self.panel())
        # self.refresh_fields()

    @staticmethod
    def loadWitnesses(app):
        return [
            {
                'key': wit['id'],
                'text': f'{wit["alias"]} | {wit["id"]}' if wit['alias'] else f'{wit["id"]}',
                'data': (wit['id'], wit['alias']),
            }
            for wit in app.witnesses
        ]
    
    @staticmethod
    def loadIdentifiers(app):
        return [
            ft.dropdown.Option(
                key=hab.pre,
                text=f'{hab.name} | {hab.pre}' if hab.name else f'{hab.pre}',
                data=hab,
            )
            for hab in app.agent.hby.habs.values()
        ]
    
    @staticmethod
    def loadContacts(app):
        org = connecting.Organizer(hby=app.agent.hby)
        contacts = org.list()
        contacts = sorted(contacts, key=lambda c: c['alias'])
        contacts = list(filter(lambda c: 'tag=witness' not in c['oobi'], contacts))
        return [
            ft.dropdown.Option(
                key=contact["id"],
                text=f'{contact["alias"]} | {contact["id"]}' if contact['alias'] else f'{contact["id"]}',
                data=contact,
            )
            for contact in contacts
        ]

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

    @log_errors
    async def create(self, _):
        if self.multisig_alias.value == '':
            await self.app.snack('Alias is required')
            return
        
        identifier = self.app.hby.habs[self.identifiersDropdown.value]
        contact = self.org.get(self.contactsDropdown.value)

        self.mhab = identifier
        self.smids = [identifier.pre, contact['id']]
        
        kwargs = dict()
        kwargs['estOnly'] = False
        kwargs['DnD'] = False

        kwargs['isith'] = int(self.keySith.value)
        kwargs['nsith'] = int(self.nkeySith.value)
        
        # Signing members and rotation members are the same for Group Multisig
        # kwargs['smids'] = self.smids
        # kwargs['rmids'] = self.smids

        # Select witnesses and set threshold
        wit_thold = self.recommendedThold(len(self.witnessList))
        kwargs['toad'] = wit_thold
        kwargs['wits'] = [wit['key'] for wit in self.witnessList]

        print("WITNESSES")
        print(kwargs['wits'])

        ghab = self.app.hby.makeGroupHab(group=self.multisig_alias.value, mhab=self.mhab, smids=self.smids,
                                        rmids=self.smids, **kwargs)

        icp = ghab.makeOwnInception(allowPartiallySigned=True)

        # Create a notification EXN message to send to the other agents
        exn, ims = grouping.multisigInceptExn(ghab.mhab,
                                                smids=ghab.smids,
                                                rmids=ghab.rmids,
                                                icp=icp)
        others = list(oset(self.smids))

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


        # hab = self.app.hby.makeHab(name=self.alias.value, **kwargs)
        # serder, _, _ = hab.getOwnEvent(sn=0)I thou
        # await self.app.snack(f'Created AID {hab.pre}.')

        # self.app.agent.witners.push(dict(serder=serder))
        await self.app.snack(f'Creating Group Multisig...')
        self.app.page.route = f'/home'
        await self.page.update_async()

    async def cancel(self, _):
        self.app.page.route = '/home'
        await self.page.update_async()

    # def refresh_fields(self):
    #     """Update the field layout based on current order."""
    #     self.lead.controls.clear()
    #     self.lead.controls.append(self.get_column(self.order[0]))
    #     self.recipient.controls.clear()
    #     self.recipient.controls.append(self.get_column(self.order[1]))

    # def get_column(self, label):
    #     if label == "yours":
    #         return ft.Row(
    #                 [
    #                     ft.Text('Your Identifier', weight=FontWeight.BOLD),
    #                     ft.Text(f'{self.hab.name} | {self.hab.pre}'),
    #                 ]
    #             )
    #     elif label == "theirs":
    #         return ft.Row(
    #                 [
    #                     ft.Text('Connecting Identifier', weight=FontWeight.BOLD),
    #                     ft.Text(self.contact),
    #                 ]
    #             )

    def swap_order(self, _):
        """Swap identifier order."""
        self.order.reverse()
        self.refresh_fields()
        self.page.update()

    def panel(self):
        self.fields_column = ft.Column()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        'Create Group Multisig',
                        weight=FontWeight.BOLD,
                        size=24
                    ),
                    ft.Row(
                        [
                            self.multisig_alias,
                        ]
                    ),
                    ft.Text(
                        'Select your Identifier',
                        weight=FontWeight.BOLD,
                        size=18
                    ),
                    self.identifiersDropdown,
                    ft.Text(
                        'Select your Contact',
                        weight=FontWeight.BOLD,
                        size=18
                    ),
                    self.contactsDropdown,
                    # ft.Row(
                    #     [
                    #         ft.TextButton("Swap Order", on_click=self.swap_order),
                    #     ]
                    # ),
                    self.keySith,
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                'Create',
                                on_click=self.create,
                            ),
                            ft.ElevatedButton(
                                'Cancel',
                                on_click=self.cancel,
                            ),
                        ]
                    ),
                ]
            ),
            expand=True,
            alignment=ft.alignment.top_left,
            padding=ft.padding.only(left=10, top=15),
        )
