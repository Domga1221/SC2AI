from asyncio.windows_events import NULL
import math
from turtle import pos
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

    pushPylonPosition = None

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
                await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.game_info.map_center, 4))

            # train probes
            if nexus.is_idle and self.can_afford(UnitTypeId.PROBE) and self.workers.amount < 23:
                nexus.train(UnitTypeId.PROBE)

            # scout
            if self.time >= 38 and not self.scout_38s: 
                await self.scout()
                self.scout_38s = True
            
            # gateway
            if (not self.structures(UnitTypeId.GATEWAY) and self.structures(UnitTypeId.WARPGATE).amount < 2 
                and not self.already_pending(UnitTypeId.GATEWAY)):
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
                await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.game_info.map_center, 7))

            # twilight council
            if not self.structures(UnitTypeId.TWILIGHTCOUNCIL) and self.can_afford(UnitTypeId.TWILIGHTCOUNCIL):
                await self.build(UnitTypeId.TWILIGHTCOUNCIL, near=self.structures(UnitTypeId.PYLON).furthest_to(nexus))

            # push pylon 
            if (self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) > 0 and self.structures(UnitTypeId.PYLON).amount == 2 
                and self.can_afford(UnitTypeId.PYLON) and self.pushPylonPosition is None):
                self.pushPylonPosition = self.enemy_start_locations[0].towards(self.game_info.map_center, 40)
                await self.build(UnitTypeId.PYLON, near=self.pushPylonPosition)
            
            # dark shrine
            if(self.structures(UnitTypeId.TWILIGHTCOUNCIL) and self.structures(UnitTypeId.PYLON).ready.amount >= 2
                and self.can_afford(UnitTypeId.DARKSHRINE) and self.structures(UnitTypeId.DARKSHRINE).amount == 0):
                await self.build(UnitTypeId.DARKSHRINE, near=self.structures(UnitTypeId.PYLON).closest_to(nexus))

            # additional gateways
            if(self.structures(UnitTypeId.DARKSHRINE) and (self.structures(UnitTypeId.WARPGATE).amount + self.structures(UnitTypeId.GATEWAY).amount) < 5):
                await self.build(UnitTypeId.GATEWAY, near=nexus)

            # darktemplars
            if(self.structures(UnitTypeId.DARKSHRINE) and self.structures(UnitTypeId.WARPGATE).ready.amount >= 1 
                and self.can_afford(UnitTypeId.DARKTEMPLAR)):
                #print("ready for darktemplar production")
                for warpgate in self.structures(UnitTypeId.WARPGATE):
                    warpgate.warp_in(UnitTypeId.DARKTEMPLAR, self.pushPylonPosition.position.random_on_distance(2))
                    '''ordered_pylons = sorted(self.structures(UnitTypeId.PYLON).ready, key=lambda pylon: pylon.distance_to(warpgate))
                    position = ordered_pylons[-1].position.random_on_distance(2)
                    placement = await self.find_placement(AbilityId.WARPGATETRAIN_DARKTEMPLAR, position, placement_step=1)
                    if placement is None:
                        print(f"can't place dark templar")
                        return
                    warpgate.warp_in(UnitTypeId.DARKTEMPLAR, placement)'''
            # zealots if not enough gas
            elif not self.can_afford(UnitTypeId.DARKTEMPLAR) and self.minerals > self.calculate_cost(UnitTypeId.DARKTEMPLAR).minerals * 4:
                for warpgate in self.structures(UnitTypeId.WARPGATE):
                    warpgate.warp_in(UnitTypeId.ZEALOT, self.pushPylonPosition.position.random_on_distance(2))

            # 4th and 5th pylon
            #if self.structures(UnitTypeId.DARKSHRINE) and self.structures(UnitTypeId.PYLON).amount <= 5:
            #   await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.game_info.map_center, 7))
            if self.already_pending(UnitTypeId.PYLON) == 0 and self.supply_left <= 4:
                await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.game_info.map_center, 10))

            # attack with dark templars
            if self.units(UnitTypeId.DARKTEMPLAR):
                #print(f"attack with dark templars")
                if self.enemy_units:
                    for darktemplar in self.units(UnitTypeId.DARKTEMPLAR):
                        closestEnemy = self.enemy_units.closest_to(darktemplar)
                        if closestEnemy.position.is_closer_than(7, darktemplar.position):
                            darktemplar.attack(self.enemy_units.closest_to(darktemplar))   
                
                elif self.enemy_structures:
                    for darktemplar in self.units(UnitTypeId.DARKTEMPLAR).idle:
                        darktemplar.attack(random.choice(self.enemy_structures))
                
                else:
                    for darktemplar in self.units(UnitTypeId.DARKTEMPLAR).idle:
                        darktemplar.attack(self.enemy_start_locations[0])

            if self.units(UnitTypeId.ZEALOT).amount >= 3 or self.units(UnitTypeId.DARKTEMPLAR).amount >= 1:
                if self.enemy_units:
                    for zealot in self.units(UnitTypeId.ZEALOT):
                        zealot.attack(self.enemy_start_locations[0])

            # idle guard
            for unit in self.units():
                if unit.is_idle:
                    # check natural
                    closestExpansion = None
                    # get closes expansion of enemy, e.g. natural expansion
                    for expansionLocation in self.expansion_locations:
                        if position.Point2(self.enemy_start_locations[0]).position.distance_to(expansionLocation) < self.EXPANSION_GAP_THRESHOLD:
                            destination = await self._client.query_pathing(self.enemy_start_locations[0], expansionLocation)
                            if destination is None:
                                continue
                            if destination < math.inf:
                                closestExpansion = expansionLocation
                                break
                    unit.attack(closestExpansion)
                    


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
