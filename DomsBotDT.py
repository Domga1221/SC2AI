from asyncio.windows_events import NULL
from sc2.bot_ai import BotAI # parent ai class to inherit from
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2 import maps
from sc2.ids.unit_typeid import UnitTypeId
import random
from sc2 import position
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.ability_id import AbilityId

class DomsBotDT(BotAI):
    scout_38s = False
    scoutingProbe_38s = NULL

    async def on_step(self, iteration: int):
        print(f"{iteration}, n_workers: {self.workers.amount}, n_idle_workers: {self.workers.idle.amount},", \
            f"minerals: {self.minerals}, gas: {self.vespene}, cannons: {self.structures(UnitTypeId.PHOTONCANNON).amount},", \
            f"pylons: {self.structures(UnitTypeId.PYLON).amount}, nexus: {self.structures(UnitTypeId.NEXUS).amount}", \
            f"gateways: {self.structures(UnitTypeId.GATEWAY).amount}, cybernetics cores: {self.structures(UnitTypeId.CYBERNETICSCORE).amount}", \
            f"stargates: {self.structures(UnitTypeId.STARGATE).amount}, dark-templar: {self.units(UnitTypeId.DARKTEMPLAR).amount}, supply: {self.supply_used}/{self.supply_cap}")

        # distribute idle workers
        await self.distribute_workers()


        if self.townhalls:
            nexus = self.townhalls[0]

            # first pylon
            if self.structures(UnitTypeId.PYLON).amount == 0 and self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus)

            # train probes
            if nexus.is_idle and self.can_afford(UnitTypeId.PROBE) and self.workers.amount < 23:
                nexus.train(UnitTypeId.PROBE)

            # scout
            if self.time >= 3 and not self.scout_38s: 
                await self.scout()
                self.scout_38s = True
            
            # gateway
            if not self.structures(UnitTypeId.GATEWAY):
                if self.can_afford(UnitTypeId.GATEWAY):
                    await self.build(UnitTypeId.GATEWAY, near=self.structures(UnitTypeId.PYLON).closest_to(nexus))

            # double assimilator
            if self.structures(UnitTypeId.ASSIMILATOR).amount < 2 and self.structures(UnitTypeId.GATEWAY):
                vespenes = self.vespene_geyser.closer_than(15, nexus)
                for vespene in vespenes:
                    if self.can_afford(UnitTypeId.ASSIMILATOR) and not self.already_pending(UnitTypeId.ASSIMILATOR):
                        await self.build(UnitTypeId.ASSIMILATOR, near=vespene)

            # cybernetics core
            if not self.structures(UnitTypeId.CYBERNETICSCORE) and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0:
                if self.can_afford(UnitTypeId.CYBERNETICSCORE):
                    await self.build(UnitTypeId.CYBERNETICSCORE, near=self.structures(UnitTypeId.PYLON).closest_to(nexus))

            # research warpgate
            if (self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(AbilityId.RESEARCH_WARPGATE) 
                and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0):
                cyberneticsCore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
                cyberneticsCore.research(UpgradeId.WARPGATERESEARCH)

            # second pylon
            if (self.structures(UnitTypeId.PYLON).ready.amount == 1 and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) > 0
                and self.can_afford(UnitTypeId.PYLON) and self.already_pending(UnitTypeId.PYLON) == 0):
                await self.build(UnitTypeId.PYLON, near=nexus)

            # train warpgate
            '''gateway = self.structures.select(UnitTypeId.GATEWAY)
            if gateway is not None:
                #print("selected gateway")
                gateway.train(UnitTypeId.WARPGATE)'''
            for gateway in self.structures(UnitTypeId.GATEWAY):
                gateway.train(UnitTypeId.WARPGATE)
            

        else:
            if self.can_afford(UnitTypeId.NEXUS):
                await self.expand_now()



    # scout 
    async def scout(self): # needs cleaning up lmao
        scoutingProbe = self.workers[0]
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 7), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 1), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 6), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 2), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 7), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 1), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 6), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 2), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 7), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 1), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 6), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 2), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 7), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 1), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 6), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 2), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 7), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 1), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 6), True)
        scoutingProbe.move(self.enemy_start_locations[0].towards(self.game_info.map_center, 2), True)
        scoutingProbe.move(self.enemy_start_locations[0] + position.Point2((random.randrange(2, 4), random.randrange(2, 4))), True)


run_game(
    maps.get("Acolyte LE"),
    [Bot(Race.Protoss, DomsBotDT()),
    Computer(Race.Protoss, Difficulty.Hard)],
    realtime=False
    #realtime=True
)
