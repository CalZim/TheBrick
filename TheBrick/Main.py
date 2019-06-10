# -*- coding: utf-8 -*-
"""
Created on Thu May 30 11:21:00 2019

@author: Caldwell Zimmerman

Basic Build:
    ling
    roach
    muta/corruptor
    broodlord


"""

from functools import reduce
from operator import or_
import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.data import race_townhalls

import enum

import math

class TheBrick(sc2.BotAI):
    #Variables go here
    step_number = 0
    
    tech_timings = [17, 40, 70, 201, 201, 201, 201, 40, 40, 41, 201] #SP, RW, HD, LD, SR, GS, UD, EC, EC, Lair, Hive
    expo_timings = [17, 28, 54]               #supply timings for an expansion
    next_expo_timing = expo_timings[0]
    gas_timings = [17, 40, 40, 40]
    next_gas_timing = gas_timings[0]
    hq = []
    
    #Macro Booleans (mostly)
    need_bases = False              #macro logic checks
    need_extractors = False
    need_sp = False
    need_bn = False
    need_rw = False
    need_hd = False
    need_ec = False
    need_lair = False
    need_overlords = True
    need_army = False
    need_drones = False
    
    dont_expand = False
    
    building_overlords = 0
    
    built_overlord = False
    built_drone = False
    
    unit_type_needed = ZERGLING
    unit_type_set = False
    
    scouting_lings = [0, 0, 0, 0]
    scouting_lings_lost = [False, False, False, False]
    
    mode = 1                        #0 obs, 1 macro, 2 micro
    macro = True
    micro = True
    
    #Tech tree stuff
    terran_tech = [False, False, False, False]           #factory, starport, armory, fusion core
    protoss_tech = []
    zerg_tech = []
    
    expansion_locations_by_distance = []
    
    #Game State Booleans (gonna be alot of these lol)    
    under_attack = False
    
    
    
    
    
    #put functions here like find enemy target or stuff
    #basic find enemy bases
    def select_target(self):
        if self.known_enemy_structures.exists:
            return random.choice(self.known_enemy_structures).position
        
        return self.enemy_start_locations[0]
    
    #get distace
    def get_distance(self, x1, y1, x2, y2):
        distance = math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))
        return distance
    
    #get enemy positions by type
    def get_enemy_positions_by_type(self, TYPE):
        positions = []
        
    
    
    #get all enemy positions
    def get_all_enemy_positions(self):
        positions = []
        for unit in self.known_enemy_units:
            positions.append(unit.position)
        return positions
    
    
    #main step code: put actions here like build worker
    async def on_step(self, iteration):
        self.step_number +=1
        if self.time < 1:
            self.hq = self.townhalls.first
            self.expansion_locations_by_distance = []
            for location in self.expansion_locations:
                x1, y1 = location.position
                x2, y2 = self.hq.position
                distance = self.get_distance(x1, y1, x2, y2)
                self.expansion_locations_by_distance.append((distance, location))
            self.expansion_locations_by_distance.sort(reverse=True)
            print(self.expansion_locations_by_distance[0][1])
            
        defending_forces = self.units(QUEEN) | self.units(ZERGLING) | self.units(ROACH) | self.units(HYDRALISK) | self.units(MUTALISK) | self.units(CORRUPTOR) | self.units(BROODLORD)
        forces = self.units(ZERGLING) | self.units(ROACH) | self.units(HYDRALISK) | self.units(MUTALISK) | self.units(CORRUPTOR) | self.units(BROODLORD)
        non_ling_forces = self.units(ROACH) | self.units(HYDRALISK) | self.units(MUTALISK) | self.units(CORRUPTOR) | self.units(BROODLORD)
        larvae = self.units(LARVA)
        larvae_count = len(larvae)
        
        self.dont_expand = False
        
        step_actions = []
        
####### TEST SPACE #################################################################################################
        
####### OBSERVATION LOGIC ##########################################################################################        
        #Observed Enemy Tech
        #Terran
        #Factory Check
        if (self.known_enemy_units(HELLION).exists or self.known_enemy_units(HELLIONTANK).exists or 
            self.known_enemy_units(CYCLONE).exists or self.known_enemy_units(SIEGETANKSIEGED).exists or
            self.known_enemy_units(SIEGETANK).exists or self.known_enemy_units(WIDOWMINE).exists or 
            self.known_enemy_units(WIDOWMINEBURROWED).exists or self.terran_tech[2] or self.terran_tech[1] or 
            self.terran_tech[3]):
            #factory exists
            self.terran_tech[0] = True
        #Starport Check
        if (self.known_enemy_units(MEDIVAC).exists or self.known_enemy_units(RAVEN).exists or 
            self.known_enemy_units(BANSHEE).exists or self.known_enemy_units(LIBERATOR).exists or
            self.known_enemy_units(LIBERATORAG).exists or self.known_enemy_units(VIKINGASSAULT).exists or
            self.known_enemy_units(VIKINGFIGHTER).exists or self.known_enemy_units(BATTLECRUISER).exists or
            self.known_enemy_structures(FACTORY).exists or self.terran_tech[3]):
            #starport exists
            self.terran_tech[1] = True
        #Armory Check
        if (self.known_enemy_units(THOR).exists or self.known_enemy_units(THORAP).exists or 
            self.known_enemy_units(HELLIONTANK).exists or self.known_enemy_structures(ARMORY).exists):
            #armory exists
            self.terran_tech[2] = True
        #Fusion Core Check
        if (self.known_enemy_units(BATTLECRUISER).exists or self.known_enemy_structures(FUSIONCORE).exists):
            #fusion core exists
            self.terran_tech[3] = True
        

        #am i under attack?
        self.under_attack = False
        for townhall in self.townhalls:
            for unit in self.known_enemy_units:
                x1, y1 = townhall.position
                x2, y2 = unit.position
                if self.get_distance(x1, y1, x2, y2) < 20:
                    print("We are under attack!! Send help!!")
                    self.under_attack = True
        
        #our army value
        army_value = self.units(ZERGLING).amount*25 + self.units(ROACH).amount*100 + self.units(HYDRALISK).amount*150
        
        #enemy bases
        enemy_base_count = (self.known_enemy_structures(NEXUS).amount + self.known_enemy_structures(HATCHERY).amount +
                            self.known_enemy_structures(LAIR).amount + self.known_enemy_structures(HIVE).amount + 
                            self.known_enemy_structures(COMMANDCENTER).amount + self.known_enemy_structures(PLANETARYFORTRESS).amount +
                            self.known_enemy_structures(ORBITALCOMMAND).amount) + 1
        print("enemy base count: " + str(enemy_base_count))            
                    
        
####### MACRO LOGIC ################################################################################################
        
        #overlords
        self.building_overlords -= 1
        if self.supply_left < len(self.townhalls)*len(self.townhalls) and self.supply_cap != 200 and self.building_overlords < 0:
            self.need_overlords = True
        else:
            self.need_overlords = False
        #tech buildings, bases, and gas
        #spawning pool
        if self.supply_used >= self.tech_timings[0]:
            if not (self.already_pending(SPAWNINGPOOL) or self.units(SPAWNINGPOOL).exists):
                self.need_sp = True
        #roach warren
        if self.supply_used >= self.tech_timings[1]:
            if not (self.already_pending(ROACHWARREN) or self.units(ROACHWARREN).exists):
                self.need_rw = True
        #hydralisk den
        if self.supply_used >= self.tech_timings[2]:
            if not (self.already_pending(HYDRALISKDEN) or self.units(HYDRALISKDEN).exists):
                self.need_hd = True
        
        #lair
        if self.supply_used >= self.tech_timings[9]:
            if not (self.already_pending(LAIR) or self.units(LAIR).exists):
                self.need_lair = True
        
        #evo chamber 1
        if self.supply_used >= self.tech_timings[7]:
            if not (self.already_pending(EVOLUTIONCHAMBER) or self.units(EVOLUTIONCHAMBER).exists):
                self.need_ec = True
        #evo chamber 2
        if self.supply_used >= self.tech_timings[8]:
            if not (self.already_pending(EVOLUTIONCHAMBER) or self.units(EVOLUTIONCHAMBER).amount > 1):
                self.need_ec = True
        
        #expansions
        for i in range(len(self.expo_timings)):
            if self.supply_used >= self.expo_timings[i]:
                if not (self.already_pending(HATCHERY) or len(self.owned_expansions) >= i+2):
                    self.need_bases = True
        if self.supply_used > 100 and not (self.need_bases or self.already_pending(HATCHERY)):
            self.need_bases = True
            for townhall in self.townhalls:
                if townhall.ideal_harvesters > townhall.assigned_harvesters:
                    self.need_bases = False
        
        #extractors
        for i in range(len(self.gas_timings)):
            if self.supply_used >= self.gas_timings[i]:
                if not (self.already_pending(EXTRACTOR) or len(self.units(EXTRACTOR)) >= i+1):
                    self.need_extractors = True
        
        #drones and units
        #drones
        self.need_workers = False
        if len(self.workers) < len(self.owned_expansions)*21:
            self.need_drones = True
        if len(self.workers) >= 60:
            self.need_drones = False
        
        #army needed? (determines if need to make units or keep droning)
        self.need_army = False
        self.unit_type_set = False
        #if we have enough workers, make units
        if len(self.workers) > 60:
            self.need_army = True
        #if under attack make units to defend
        if self.under_attack:
            self.need_army = True
        #make some units to defend early aggression
        if self.supply_used > 20 and len(forces) < 6:
            self.need_army = True
        #make units v make drones based of enemy bases
        #fix/add this
        #alter base timings based on enemy bases
        if self.townhalls.amount > enemy_base_count + 1:
            self.dont_expand = True
            if self.workers.amount > self.townhalls.amount*14 - 12:
                self.need_army = True
        
            
        print("dont expand: " + str(self.dont_expand))
        #make lings for scouting
        if len(self.units(ZERGLING)) < 4 and self.supply_used > 20:
            self.need_army = True
            self.unit_type_needed = ZERGLING
            self.unit_type_set = True
        print("workers: " + str(self.workers.amount))
        print("army value: " + str(army_value))
        print("need army: " + str(self.need_army))
        print("roach warren is ready: " + str(self.units(ROACHWARREN).ready.exists))
        
        #unit type needed
        if not self.unit_type_set:
            if self.units(HYDRALISKDEN).exists and self.units(HYDRALISKDEN).ready:
                if not self.units(HYDRALISK).exists:
                    self.unit_type_needed = HYDRALISK
                elif len(self.units(ROACH))/len(self.units(HYDRALISK)) > 1:
                    self.unit_type_needed = HYDRALISK
                else:
                    self.unit_type_needed = ROACH
            elif self.units(ROACHWARREN).ready.exists:
                self.unit_type_needed = ROACH
            elif self.units(SPAWNINGPOOL).ready.exists:
                self.unit_type_needed = ZERGLING
        #if need army we dont need drones
        if self.need_army:
            self.need_drone = False
        
####### Base Manegment stuff ########################################################################################
        #make queens: makes 2 per base (in quantity not location)
        if len(self.units(QUEEN)) < len(self.owned_expansions)*2:
            if self.can_afford(QUEEN) and self.units(HATCHERY).idle.exists:
                step_actions.append(self.units(HATCHERY).idle.random.train(QUEEN))
        #queen injects
        for townhall in self.townhalls:
            if not townhall.has_buff(BuffId.QUEENSPAWNLARVATIMER):
                queens_with_enough_energy = self.units.filter(lambda unit: unit.type_id == QUEEN and unit.energy >= 25)
                if queens_with_enough_energy.idle.exists:
                    queen = queens_with_enough_energy.idle.closest_to(townhall)
                    step_actions.append(queen(EFFECT_INJECTLARVA, townhall))
        
        #creep spread
        #ill do this later lol its pretty hard to even make a bad system
        
        #upgrade (might move this somewhere else at some point but its here for now)
        #if self.units(EVOLUTIONCHAMBER).ready.idle.exists:
         #   if self.can_afford(RESEARCH_ZERGMISSILEWEAPONSLEVEL1):
          #      self.units(EVOLUTIONCHAMBER).ready.idle.random.research(RESEARCH_ZERGMISSILEWEAPONSLEVEL1)
        
        #extractor drones
        for a in self.units(EXTRACTOR):
            if a.assigned_harvesters < a.ideal_harvesters:
                step_actions.append(self.workers.random.gather(a))
        
        #mineral rallys
        for townhall in self.townhalls:
            if townhall.assigned_harvesters < townhall.ideal_harvesters:
                step_actions.append(townhall(RALLY_HATCHERY_WORKERS, self.state.units.mineral_field.closest_to(townhall)))
            else: 
                townhalls_need_workers = self.units.filter(lambda unit: unit.type_id == HATCHERY and unit.assigned_harvesters < unit.ideal_harvesters)
                if townhalls_need_workers.exists:
                    step_actions.append(townhall(RALLY_HATCHERY_WORKERS, self.state.units.mineral_field.closest_to(townhalls_need_workers.random)))
            if townhall.assigned_harvesters > townhall.ideal_harvesters:
                townhalls_need_workers = self.units.filter(lambda unit: unit.type_id == HATCHERY and unit.assigned_harvesters < unit.ideal_harvesters)
                if townhalls_need_workers.exists:
                    step_actions.append(self.workers.closest_to(townhall).gather(self.state.units.mineral_field.closest_to(townhalls_need_workers.random)))
        #idle workers
        for worker in self.workers.idle:
            step_actions.append(worker.gather(self.state.units.mineral_field.closest_to(self.townhalls.closest_to(worker))))
        
        #scouting
        #this is also much harder than one would think
        if self.step_number % 120 == 0:
            if len(self.units(ZERGLING)) > 3:
                step_actions.append(self.units(ZERGLING)[0].move(self.expansion_locations_by_distance[1][1]))
                self.scouting_lings[0] = self.units(ZERGLING)[0]
                step_actions.append(self.units(ZERGLING)[1].move(self.expansion_locations_by_distance[2][1]))
                self.scouting_lings[1] = self.units(ZERGLING)[1]
                step_actions.append(self.units(ZERGLING)[2].move(self.expansion_locations_by_distance[3][1]))
                self.scouting_lings[2] = self.units(ZERGLING)[2]
                step_actions.append(self.units(ZERGLING)[3].move(self.expansion_locations_by_distance[4][1]))
                self.scouting_lings[3] = self.units(ZERGLING)[3]
        if (self.step_number - 1) % 120 == 0:
            self.scouting_lings_lost = [False, False, False, False]
            for i in range(len(self.scouting_lings)):
                ling_exists = False
                for unit in self.units(ZERGLING):
                    if self.scouting_lings[i].tag == unit.tag:
                        ling_exists = True
                        print("ling exists")
                if not ling_exists:
                    self.scouting_lings_lost[i] = True
        
        
        
######## MACRO STUFF ################################################################################################
        if self.mode == 1:
            self.macro = True
            #Expansions
            if self.need_bases and self.macro and not self.under_attack and not self.dont_expand:
                if self.can_afford(HATCHERY):
                    self.need_bases = False
                    print("expanding")
                    await self.expand_now(HATCHERY)
                else:
                    self.macro = False
            #Extractors
            if self.need_extractors and self.macro and not self.under_attack:
                if self.can_afford(EXTRACTOR):
                    self.need_extractors = False
                    drone = self.workers.random
                    target = self.state.vespene_geyser.closest_to(self.townhalls.random.position)
                    step_actions.append(drone.build(EXTRACTOR, target))
                else:
                    self.macro = False
                    
            
            #Tech Buildings
            #Spawning Pool
            if self.need_sp and self.macro:
                if self.can_afford(SPAWNINGPOOL):
                    self.need_sp = False
                    await self.build(SPAWNINGPOOL, near=self.hq)
                else:
                    self.macro = False
            #Baneling Nest
            if self.need_bn and self.macro:
                if self.can_afford(BANELINGNEST):
                    self.need_bn = False
                    await self.build(BANELINGNEST, near=self.hq)
                else:
                    self.macro = False
            #Roach Warren
            if self.need_rw and self.macro:
                if self.can_afford(ROACHWARREN):
                    self.need_rw = False
                    await self.build(ROACHWARREN, near=self.hq)
                else:
                    self.macro = False
            #Hydralisk Den
            if self.need_hd and self.macro:
                if self.can_afford(HYDRALISKDEN):
                    self.need_hd = False
                    await self.build(HYDRALISKDEN, near=self.hq)
                else:
                    self.macro = False
            #Evolution Chamber
            if self.need_ec and self.macro:
                if self.can_afford(EVOLUTIONCHAMBER):
                    self.need_ec = False
                    await self.build(EVOLUTIONCHAMBER, near=self.hq)
                else:
                    self.macro = False
            #Lair
            if self.need_lair and self.macro:
                if self.can_afford(LAIR):
                    self.need_hd = False
                    step_actions.append(self.hq.build(LAIR))
                else:
                    self.macro = False
            
            
            
            #Units
            #Overlords
            self.built_overlord = False
            if self.need_overlords and self.macro:
                if self.can_afford(OVERLORD) and (larvae_count > 0):
                    self.need_overlords = False
                    larvae_count -=1
                    self.built_overlord = True
                    self.building_overlords = 60 - len(self.townhalls)*10
                    step_actions.append(larvae.random.train(OVERLORD))
                else:
                    self.macro = False
            print("do we need army?")
            print(self.need_army)
            #army
            if self.need_army and self.macro and self.supply_left > 0:
                if self.can_afford(self.unit_type_needed) and (larvae_count > 0):
                    print("building units")
                    self.need_army = False
                    self.macro = False
                    larvae_count -=1
                    step_actions.append(larvae.random.train(self.unit_type_needed))
                else:
                        self.macro = False  
            print("do we need drones?")
            print(self.need_drones)
            #drones
            self.built_drone = False
            if self.need_drones and self.macro and self.supply_left > 0:
                if self.can_afford(DRONE) and (larvae_count > 0):
                    print("building drones")
                    self.need_drones = False
                    larvae_count -=1
                    self.built_drone = True
                    step_actions.append(larvae.random.train(DRONE))
                else:
                    self.macro = False
            
            #else build army
            if self.macro and larvae_count > 0 and not (self.built_drone or self.built_overlord) and self.supply_left > 0:
                print("default to build army")
                #make units
                if self.can_afford(self.unit_type_needed):
                    print("building default")
                    step_actions.append(larvae.random.train(self.unit_type_needed))
            
            #next mode
            self.mode = 2
            
            
####### MICRO ######################################################################################################
        if self.mode == 2:
            #do the micro stuff
            #if maxed go kill them
            #if under attack, defend plz lol (needs improved)
            if self.under_attack:
                if self.known_enemy_units.exists:
                    attacking_units = []
                    for enemy_unit in self.known_enemy_units:
                        for townhall in self.townhalls:
                            x1, y1 = townhall.position
                            x2, y2 = enemy_unit.position
                            if self.get_distance(x1, y1, x2, y2) < 20:
                                attacking_units.append(enemy_unit)
                    if len(attacking_units) > len(defending_forces) and self.time < 120:
                        for unit in defending_forces.idle:
                            step_actions.append(unit.attack(random.choice(attacking_units)))
                        for drone in self.units(DRONE).closer_than(10, random.choice(attacking_units)):
                            step_actions.append(drone.attack(random.choice(attacking_units)))
                    elif len(attacking_units) > 0:
                        for unit in defending_forces.idle:
                            step_actions.append(unit.attack(random.choice(attacking_units)))    
            #if max in the enternal words of Freddy, "send army to rekt enemy ggez XD"
            elif self.supply_used > 195:
                for unit in forces.idle:
                    step_actions.append(unit.attack(self.select_target()))
            
            if self.supply_used < 170 and not self.under_attack:
                far_units = self.units(ROACH).further_than(90, self.hq) | self.units(HYDRALISK).further_than(50, self.hq)
                for unit in far_units:
                    step_actions.append(unit.move(self.townhalls.closest_to(unit).position))
            for queen in self.units(QUEEN):
                x1, y1 = queen.position
                x2, y2 = self.townhalls.closest_to(queen).position
                distance = self.get_distance(x1, y1, x2, y2)
                if distance > 40:
                    step_actions.append(queen.move(self.townhalls.closest_to(queen).position))
            
            self.mode = 1
            
             
            
        
        #end
        await self.do_actions(step_actions)
        

def main():
    sc2.run_game(sc2.maps.get("BlueshiftLE"), [ 
        Bot(Race.Zerg, TheBrick()),
        Computer(Race.Protoss, Difficulty.Hard) # COMPUTER OPPONENT - Difficulty {  VeryEasy = 1;  Easy = 2;  Medium = 3;  MediumHard = 4;  Hard = 5;  Harder = 6;  VeryHard = 7;  CheatVision = 8;  CheatMoney = 9;  CheatInsane = 10;}
    ], realtime=False)

if __name__ == '__main__':
    main()