module Generator

import IO;
import Set;
import List;
import String;
import Location;
import Set;
import Map;

import Syntax;
import Parser;
import Checker;

void main() {
    inFile = |project://rascaldsl/instance/spec1.tdsl|;
    cst = parsePlanning(inFile);
    rVal = generator(cst);
    println(rVal);
}

DefInfo findReference(tm, use) {
    return findReferenceFromSrc(tm, use.src);
}

DefInfo findReferenceFromSrc(TModel tm, src) {
    defs = getUseDef(tm);
    if (def <- defs[src]) { 
        return tm.definitions[def].defInfo;
    }
    throw "Fix references in language instance";
}

str generator(cst) { // WIP
    tm = modulesTModelFromTree(cst);
    retVal = "";
    trigger_list = [];
    action_list = [];
    if(/(RoverConfig) `Rover: <IDList missions> MAC: <STR mac>` := cst) {
        
        bhv_list = extractBhvs(missions, tm);
        bhv_def = printBhvDef(bhv_list, tm);
        retVal = "
        '<mac>
        '
        '<bhv_list>
        '
        '<bhv_def>
        '
        '
        '";
    }
        // '<generateBhvsFromMissions(missions, tm)>

        // '<for (<mission> <- {<id> |/(ID) `<ID id>` := missions}) {>
        // '<mission>:<printMission(mission, tm)>
        // '<}>
    return retVal;
}


list[loc] extractBhvs(missions, tm) {
    bhvs = ();
    for (<mission> <- {<id> |/(ID) `<ID id>` := missions}) {
        DefInfo defInfo = findReference(tm, mission);
        if (miss <- defInfo.mission) {
            for (behavior <- miss.behaviorList) {
                if(getContent(behavior) notin bhvs)
                bhvs += (getContent(behavior): behavior);
            }
        }
    }

    return [bhvs[bhv] | bhv <- bhvs];
}

// tuple[list[str], list[str]] generateComponentsFromBhvs(bhv_list, tm) {
//     trigger_list = ["try", "simple"];
//     action_list = ["try", "simple", "action"];

//     return <trigger_list, action_list>;
// }


str printTriggers(list[str] trigger_list, list_mod) {
    retVal = [];
    for (trigger <- trigger_list) {
        retVal += "<trigger>";
    }
    if (list_mod == "ANY")
        return intercalate(" or ", retVal);
    else 
        return intercalate(" and ", retVal);
}

str printActions(list[str] action_list) {
    retVal = [];
    for (action <- action_list) {
        retVal += "lambda: <action>";
    }
    return "[" + intercalate(", ", retVal) + "]";
}

str printBhvDef(list[loc] bhv_list, tm) {
    trigger_map = ();
    action_map = ();
    retVal = [];
    for (bhvSrc <- bhv_list) {
        DefInfo defInfo = findReferenceFromSrc(tm, bhvSrc);
        bhv_str = getContent(bhvSrc);
        if (bhv <- defInfo.behavior) {
            
            trigger_list = [];
            for (trigger <- bhv.triggerList) {
                tmp_ret = generateTriggerFromId(tm, trigger, trigger_map);
                trigger_list += tmp_ret[0];
                trigger_map = tmp_ret[1];
            }
            trigger_list = toList(toSet(trigger_list));
            action_list = [];
            for (action <- bhv.actionList) {
                tmp_ret = generateActionFromId(tm, action, action_map);
                action_list += tmp_ret[0];
                action_map = tmp_ret[1];
            }

            retVal += "
            'class <bhv_str>(Behavior):
            '\tdef __init__(self):
            '\t\tBehavior.__init__(self)
            '\t\tself.has_fired = False
            '\t\tself.suppresed = False
            '
            '\tdef check(self):
            '\t\tself.has_fired = <printTriggers(trigger_list, bhv.triggerListMod)>
            '\t\treturn self.has_fired
            '
            '\tdef action(self):
            '\t\tself.suppresed = False
            '\t\t<printActions(action_list)>
            '
            '
            '
            '
            '
            '<trigger_map>
            '<action_map>
            '";

        }
    }
    return intercalate("\n\n\n", retVal);
}



// str printMission(mission, tm) {
//     DefInfo defInfo = findReference(tm, mission);
//     retVal = ["CONTROLLER = Controller(return_when_no_action=True)"];
    
//     if (miss <- defInfo.mission) {
//         retVal += "<miss>";
//     }

//     return intercalate("\n", retVal);
// }


tuple[list[str], map[str, list[str]]] generateTriggerFromId(tm, startIdSrc, map[str, list[str]] trigger_map) {
    retVal = [];
    trigger_str = getContent(startIdSrc);

    if (trigger_str in trigger_map) {
        retVal += trigger_map[trigger_str];
        return <retVal, trigger_map>;
    }
    DefInfo defInfo = findReferenceFromSrc(tm, startIdSrc);
    if (l <- defInfo.idList) {
        for (idSrc <- l.idList) {
            tmp_ret = generateTriggerFromId(tm, idSrc, trigger_map);
            retVal += tmp_ret[0];
            trigger_map = tmp_ret[1];
        }
    }
    else if (ct <- defInfo.colorTrigger) {retVal += "<ct>"; }
    else if (dt <- defInfo.distanceTrigger) {retVal += "<dt>"; }
    else if (tt <- defInfo.touchTrigger) {retVal += "<tt>"; }

    trigger_map += (trigger_str: retVal);
    return <retVal, trigger_map>;
}

tuple[list[str], map[str, list[str]]] generateActionFromId(tm, startIdSrc, map[str, list[str]] action_map) {
    retVal = [];
    action_str = getContent(startIdSrc);

    if (action_str in action_map) {
        retVal += action_map[action_str];
        return <retVal, action_map>;
    }
    DefInfo defInfo = findReferenceFromSrc(tm, startIdSrc);
    if (l <- defInfo.idList) {
        for (idSrc <- l.idList) {
            tmp_ret = generateActionFromId(tm, idSrc, action_map);
            retVal += tmp_ret[0];
            action_map = tmp_ret[1];
        }
    }
    else if (ma <- defInfo.moveAction) {retVal += "<ma>"; }
    else if (ta <- defInfo.turnAction) {retVal += "<ta>"; }
    else if (sa <- defInfo.speakAction) {retVal += "<sa>"; }
    else if (la <- defInfo.ledAction) {retVal += "<la>"; }

    action_map += (action_str: retVal);
    return <retVal, action_map>;
}

// str printTriggerIDList(idList) {
//     retVal = [];
//     for (<id> <- {<id> |/(ID) `<ID id>` := idList}) {
//         retVal += "<id>()";
//     }
//     return intercalate(" and ", retVal);
// }

// str printTriggerIDList(idList, listMod) {
//     retVal = [];
//     for (<id> <- {<id> |/(ID) `<ID id>` := idList}) {
//         retVal += "<id>()";
//     }
//     if ("<listMod>" == "ANY")
//         return intercalate(" or ", retVal);
//     else 
//         return intercalate(" and ", retVal);
// }

// // str printBehaviorIDList(idList) {
// //     retVal = [];
// //     for (<id> <- {<id> |/(ID) `<ID id>` := idList}) {
// //         retVal += "CONTROLLER.ADD(<id>())";
// //     }
// //     return intercalate("\n", retVal);
// // }

// // str printActionIDList(idList, for_bhv) {
// //     retVal = [];
// //     if (for_bhv == false){
// //         for (<id> <- {<id> |/(ID) `<ID id>` := idList}) {
// //         retVal += "<id>()";
// //     }
// //     }
// //     else {
// //         for (<id> <- {<id> |/(ID) `<ID id>` := idList}) {
// //             retVal += "if not self.suppressed:
// //             '\t<id>()
// //             '\twhile MOTOR.is_running and not self.supressed:
// //             '\t\tpass
// //             ";
// //         }
// //     }
// //     return intercalate("\n\t", retVal);
// // }

// str printTriggerDef(ast) {
//     retVal = [];
//     for (<id, t> <- {<idNew, roverTrigger> | /(Trigger) `<ID idNew> <TriggerAssignment triggerAssignment> <RoverTrigger roverTrigger>` := ast}) {
//         retVal += "def <id>(): <printTriggerCode(t)>";
//     }
//     for (<id, l> <- {<idNew, idList> | /(Trigger) `<ID idNew> <TriggerAssignment triggerAssignment> <IDList idList>` := ast}) {
//         retVal += "def <id>():\n\treturn <printTriggerIDList(l)>";
//     }
//     return intercalate("\n", retVal);
// }


// str printTriggerCode(trigger) {
//     if(/(ColorTrigger)`COLOR <ColorReadable color>` := trigger) return "return read_color_sensor(CS) == \"<color>\"";
//     if(/(DistanceTrigger)`INDISTANCE <NATURAL distance>` := trigger) return "return read_distance_sensor(ULT_S) \<= <distance>";
// //     if(/(TouchTrigger)`TOUCH <TouchSensor touchSensor>`:= trigger) {
// //         if(/(TouchSensor)`right` := touchSensor) return "return read_touch_sensor(TOUCH_R)";
// //         if(/(TouchSensor)`left` := touchSensor) return "return read_touch_sensor(TOUCH_L)";
// //         if(/(TouchSensor)`any` := touchSensor) return "return read_touch_sensor(TOUCH_R) or read_touch_sensor(TOUCH_L)";
// //     }
//     return "return False";
// }


// // str printActionDef(ast) {
// //     retVal = [];
// //     for (<id, a> <- {<idNew, roverAction> | /(Action) `<ID idNew> <ActionAssignment actionAssignment> <RoverAction roverAction>` := ast}) {
// //         retVal += "def <id>(): <printRoverAction(a)>";
// //     }
// //     for (<id, l> <- {<idNew, idList> | /(Action) `<ID idNew> <ActionAssignment actionAssignment> <IDList idList>` := ast}) {
// //         retVal += "def <id>():\n\t<printActionIDList(l, false)>";
// //     }
// //     return intercalate("\n", retVal);
// // }

// // // str printRoverAction(action) {
// // //     if(/(MoveAction)`FORWARD <NATURAL distance>` := action) return "MOTOR.run(rotations=<distance>)";
// // //     if(/(MoveAction)`BACKWARD <NATURAL distance>` := action) return "MOTOR.run(forward=False, rotations=<distance>)";
// // //     if(/(TurnAction)`TURN <ANGLE angle>` := action) return "MOTOR.turn(direction=<angle>)"; // implement the conversion from [-180;180] to [-100; 100]
// // //     if(/(SpeakAction)`SPEAK <STR text>` := action) return "S.speak(<text>)";
// // //     if(/(SpeakAction)`BEEP` := action) return "S.beep()";
// // //     if(/(LedAction)`LED <ColorWritable color>` := action) return "set_led(LEDS, \"<color>\")";
// // //     return "";
// // // }


// // str printBehaviorDef(ast) {
// //     retVal = [];
// //     for (<b, t, a> <- {<idBhv, idTrig, idAct> | /(Behavior) `Behavior: <ID idBhv> WHEN <ID idTrig> DO <ID idAct>` := ast}) {
// //         retVal += "
// //         'class <b>(Behavior):
// //         '\tdef __init__(self):
// //         '\t\tBehavior.__init__(self)
// //         '\t\tself.has_fired = False
// //         '\t\tself.suppresed = False
// //         '
// //         '\tdef check(self):
// //         '\t\tself.has_fired = <t>()
// //         '\t\treturn self.has_fired
// //         '
// //         '\tdef action(self):
// //         '\t\tself.suppresed = False
// //         '\t\t<a>()
// //         '\t\twhile MOTOR.is_running and not self.supressed:
// //         '\t\t\tpass
// //         '\t\tif not self.supressed:
// //         '\t\t\treturn True
// //         '\t\telse:
// //         '\t\t\ttimedlog(\"<b> suppressed\")
// //         '\t\t\treturn False
// //         '
// //         '\tdef suppress(self):
// //         '\t\tMOTOR.stop()
// //         '\t\tself.supressed = True
// //         '";
// //     }
// //     for (<b, t, la> <- {<idBhv, idTrig, listAction> | /(Behavior) `Behavior: <ID idBhv> WHEN <ID idTrig> DO <IDList listAction>` := ast}) {
// //         retVal += "
// //         'class <b>(Behavior):
// //         '\tdef __init__(self):
// //         '\t\tBehavior.__init__(self)
// //         '\t\tself.has_fired = False
// //         '\t\tself.suppresed = False
// //         '
// //         '\tdef check(self):
// //         '\t\tself.has_fired = <t>()
// //         '\t\treturn self.has_fired
// //         '
// //         '\tdef action(self):
// //         '\t\tself.suppresed = False
// //         '\t\t<printActionIDList(la, true)>
// //         '\t\tif not self.supressed:
// //         '\t\t\treturn True
// //         '\t\telse:
// //         '\t\t\ttimedlog(\"<b> suppressed\")
// //         '\t\t\treturn False
// //         '
// //         '\tdef suppress(self):
// //         '\t\tMOTOR.stop()
// //         '\t\tself.supressed = True
// //         '";
// //     }
// //     for (<b, lm, lt, a> <- {<idBhv, listMod, listTrig, idAct> | /(Behavior) `Behavior: <ID idBhv> WHEN <ListMod listMod> <IDList listTrig> DO <ID idAct>` := ast}) {
// //         retVal += "
// //         'class <b>(Behavior):
// //         '\tdef __init__(self):
// //         '\t\tBehavior.__init__(self)
// //         '\t\tself.has_fired = False
// //         '\t\tself.suppresed = False
// //         '
// //         '\tdef check(self):
// //         '\t\tself.has_fired = <printTriggerIDList(lt, lm)>
// //         '\t\treturn self.has_fired
// //         '
// //         '\tdef action(self):
// //         '\t\tself.suppresed = False
// //         '\t\t<a>()
// //         '\t\twhile MOTOR.is_running and not self.supressed:
// //         '\t\t\tpass
// //         '\t\tif not self.supressed:
// //         '\t\t\treturn True
// //         '\t\telse:
// //         '\t\t\ttimedlog(\"<b> suppressed\")
// //         '\t\t\treturn False
// //         '
// //         '\tdef suppress(self):
// //         '\t\tMOTOR.stop()
// //         '\t\tself.supressed = True
// //         '";
// //     }
// //     for (<b, lm, lt, la> <- {<idBhv, listMod, listTrig, lAct> | /(Behavior) `Behavior: <ID idBhv> WHEN <ListMod listMod> <IDList listTrig> DO <IDList lAct>` := ast}) {
// //         retVal += "
// //         'class <b>(Behavior):
// //         '\tdef __init__(self):
// //         '\t\tBehavior.__init__(self)
// //         '\t\tself.has_fired = False
// //         '\t\tself.suppresed = False
// //         '
// //         '\tdef check(self):
// //         '\t\tself.has_fired = <printTriggerIDList(lt, lm)>
// //         '\t\treturn self.has_fired
// //         '
// //         '\tdef action(self):
// //         '\t\tself.suppresed = False
// //         '\t\t<printActionIDList(la, true)>
// //         '\t\tif not self.supressed:
// //         '\t\t\treturn True
// //         '\t\telse:
// //         '\t\t\ttimedlog(\"<b> suppressed\")
// //         '\t\t\treturn False
// //         '
// //         '\tdef suppress(self):
// //         '\t\tMOTOR.stop()
// //         '\t\tself.supressed = True
// //         '";
// //     }
// //     return intercalate("\n", retVal);
// // }


// // str printTaskBhv(task_cond, name) {
// //     retVal = "TASK_REGISTRY.add(<name>)
// //     'class Update<name>(Behavior):
// //     '\tdef __init__(self):
// //     '\t\tBehavior.__init__(self)
// //     '
// //     '\tdef check(self):
// //     'return not TASK_REGISTRY.get(<name>) and <task_cond>();
// //     '
// //     '\tdef action(self):
// //     '\t\tTASK_REGISTRY.set(<name>, True)
// //     '\t\treturn True
// //     '
// //     '\tdef suppress(self):
// //     '\t\tpass
// //     '";
// //     return retVal;
// // }

// // str printTaskListBhv(task_list, list_mod, name) {
// //     retVal = "TASK_REGISTRY.add(<name>)
// //     'class Update<name>(Behavior):
// //     '\tdef __init__(self):
// //     '\t\tBehavior.__init__(self)
// //     '
// //     '\tdef check(self):
// //     'return not TASK_REGISTRY.get(<name>) and <printTriggerIDList(task_list, list_mod)>;
// //     '
// //     '\tdef action(self):
// //     '\t\tTASK_REGISTRY.set(<name>, True)
// //     '\t\treturn True
// //     '
// //     '\tdef suppress(self):
// //     '\t\tpass
// //     '";
// //     return retVal;
// // }

// // str printMissionDef(ast) {
// //     retVal = [];
// //     name = "main";
// //     for (<t, b> <- {<idTask, idBhv> | /(Mission) `Mission: <ID idTask> WHILE <ID idBhv>` := ast}) {
// //         // retVal += "<printTaskBhv(t, name)>
// //         // 'CONTROLLER.add(<b>())
// //         // 'CONTROLLER.add(Update<name>())
// //         // ";
// //         retVal += "AAAAA";
// //     }
// //     for (<t, lb> <- {<idTask, listBhv> | /(Mission) `Mission: <ID idTask> WHILE <IDList listBhv>` := ast}) {
// //         retVal += "<printTaskBhv(t, name)>
// //         '<printBehaviorIDList(lb)>
// //         'CONTROLLER.add(Update<name>())
// //         ";
// //     }
// //     for (<lm, lt, b> <- {<listMod, listTask, idBhv> | /(Mission) `Mission: <ListMod listMod> <IDList listTask> WHILE <ID idBhv>` := ast}) {
// //         retVal += "<printTaskListBhv(lt, lm, name)>
// //         'CONTROLLER.add(<b>())
// //         'CONTROLLER.add(Update<name>())
// //         ";
// //     }
// //     for (<lm, lt, lb> <- {<listMod, listTask, listBhv> | /(Mission) `Mission: <ListMod listMod> <IDList listTask> WHILE <IDList listBhv>` := ast}) {
// //         retVal += "<printTaskListBhv(lt, lm, name)>
// //         '<printBehaviorIDList(lb)>
// //         'CONTROLLER.add(Update<name>())
// //         ";
// //     }
// //     return intercalate("\n", retVal);
// // }

