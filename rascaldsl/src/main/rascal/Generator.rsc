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
        tmp_ret = generateBhvsDef(bhv_list, tm);
        bhv_def = tmp_ret[0];
        trigger_map = tmp_ret[1];
        retVal = "
        '<mac>
        '
        '<bhv_list>
        '
        '<bhv_def>
        '
        '
        '<generateMissionsDef(missions, tm, trigger_map)>
        '
        '
        '<printMissionsUsage(missions, tm)>
        '";
    }

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

str printListLambda(list[str] input_list) {
    retVal = [];
    for (elem <- input_list) {
        retVal += "lambda: <elem>";
    }
    return "[" + intercalate(", ", retVal) + "]";
}

tuple[str, map[str, list[str]]] generateBhvsDef(list[loc] bhv_list, tm) {
    trigger_map = ();
    action_map = ();
    retVal = [];
    for (bhvSrc <- bhv_list) {
        DefInfo defInfo = findReferenceFromSrc(tm, bhvSrc);
        bhv_str = getContent(bhvSrc);
        if (bhv <- defInfo.behavior) {
            
            trigger_list = [];
            for (trigger <- bhv.triggerList) {
                tmp_ret = extractComponentFromId(tm, trigger, trigger_map, generateTrigger);
                trigger_list += tmp_ret[0];
                trigger_map = tmp_ret[1];
            }
            action_list = [];
            for (action <- bhv.actionList) {
                tmp_ret = extractComponentFromId(tm, action, action_map, generateAction);
                action_list += tmp_ret[0];
                action_map = tmp_ret[1];
            }

            states_init = [];
            states_check = [];
            if (bhv.triggerListMod == "ALLORD") {
                states_init += "self.has_fired = False";
                states_init += "self.counter_conds = 0";
                states_init += "self.trigger_list = <printListLambda(trigger_list)>";

                states_check += "
                'if self.trigger_list[self.counter_conds]():
                '\tself.counter_conds += 1
                'if self.counter_conds == <size(trigger_list)>:
                '\tself.operations = <printListLambda(action_list)>
                '\treturn True
                '";

            }
            else {
                trigger_list = toList(toSet(trigger_list));
                states_init += "self.has_fired = False";
                states_check += "fire_cond = (<printTriggers(trigger_list, bhv.triggerListMod)>)
                'if fire_cond != self.has_fired:
                '\tself.has_fired = fire_cond
                '\tif self.has_fired:
                '\t\tself.operations = <printListLambda(action_list)>
                '\t\treturn True
                '";
            }
            retVal += "<printBhvDef(intercalate("\n", states_init), intercalate("\n", states_check), bhv_str)>";

        }
    }
    return <intercalate("\n\n\n", retVal), trigger_map>;
}

str printBhvDef(states_init, states_check, bhv_str) {
    return "
    'class <bhv_str>_bhv(Behavior):
    '\tdef __init__(self):
    '\t\tBehavior.__init__(self)
    '\t\tself.suppresed = False
    '\t\tself.operations = []
    '\t\t<states_init>
    '
    '
    '\tdef _reset(self):
    '\t\tself.operations = []
    '\t\tMOTOR.stop()
    '\t\tif not self.suppresed:
    '\t\t\t<states_init>
    '
    '
    '\tdef check(self):
    '\t\t<states_check>
    '\t\treturn False
    '
    '
    '\tdef action(self):
    '\t\tself.suppresed = False
    '\t\tif DEBUG:
    '\t\t\ttimedlog(\"<bhv_str> fired\")
    '
    '\t\tfor operation in self.operations:
    '\t\t\toperation()
    '\t\t\twhile MOTOR.is_running and not self.supressed:
    '\t\t\t\tpass
    '\t\t\tif self.supressed:
    '\t\t\t\tbreak
    '
    '\t\tself._reset()
    '
    '\t\tif DEBUG and not self.supressed:
    '\t\t\ttimedlog(\"<bhv_str> done\")
    '\t\treturn not self.supressed
    '
    '
    '\tdef suppress(self):
    '\t\tMOTOR.stop()
    '\t\tself.supressed = True
    '\t\tif DEBUG:
    '\t\t\ttimedlog(\"<bhv_str> suppressed\")
    '";
}


str printTaskBhv(list[value] task_list, task_list_mod, mission_name) {
    
    list[str] states_init = [];
    list[str] states_check = [];
    if (task_list_mod == "ANY") {
        states_init += "TASK_REGISTRY.add(\"ANY\")";
        states_check += "TASK_REGISTRY.update(\"ANY\", (<printTriggers(task_list, task_list_mod)>))";
    }
    else if (task_list_mod == "ALL") {
        int cont = 0;
        for (trigger <- task_list) {
            cont = cont + 1;
            states_init += "TASK_REGISTRY.add(\"state_<cont> \")";
            states_check += "TASK_REGISTRY.update(\"state_<cont> \", (<trigger>))";
        }
    }
    else {
        states_init += "TASK_REGISTRY.add(\"ALLORD\")";
        states_init += "self.counter_task = 0";
        states_init += "self.task_list = <printListLambda(task_list)>";

        states_check += "
        'if self.task_list[self.counter_task]():
        '\tself.counter_task += 1
        'if self.counter_task == <size(task_list)>:
        '\tTASK_REGISTRY.update(\"ALLORD\", True)
        '";

    }

    retVal = "
    'class <mission_name>_updateTasksBhv(Behavior):
    '\tdef __init__(self):
    '\t\tBehavior.__init__(self)
    '\t\t<intercalate("\n", states_init)>
    '
    '\tdef check(self):
    '\t\t<intercalate("\n", states_check)>
    '\t\treturn False
    '
    '\tdef action(self):
    '\t\treturn True
    '
    '\tdef suppress(self):
    '\t\tpass
    '";
    return retVal;
}

str generateMissionsDef(missions, tm, trigger_map) {
    retVal = [];
    for (<mission> <- {<id> |/(ID) `<ID id>` := missions}) {
        DefInfo defInfo = findReference(tm, mission);
        if (miss <- defInfo.mission) {
            task_list = [];
            for (trigger <- miss.taskList) {
                tmp_ret = extractComponentFromId(tm, trigger, trigger_map, generateTrigger);
                task_list += tmp_ret[0];
                trigger_map = tmp_ret[1];
            }

            if (miss.taskListMod != "ALLORD")   task_list = toList(toSet(task_list));


            retVal += "<printTaskBhv(task_list, miss.taskListMod, "<mission>")>";
        }
    }
    return intercalate("\n", retVal);
}

str printMissionsUsage(missions, tm) {
    retVal = [];
    for (<mission> <- {<id> |/(ID) `<ID id>` := missions}) {
        DefInfo defInfo = findReference(tm, mission);
        if (miss <- defInfo.mission) {
            retVal += "CONTROLLER = Controller(return_when_no_action=True)
            'TASK_REGISTRY = TaskRegistry()
            'CONTROLLER.add(<mission>_updateTasksBhv())
            '";

            for (behavior <- miss.behaviorList) {
                retVal += "CONTROLLER.add(<getContent(behavior)>_bhv())";
            }
            retVal += "bluetooth_connection.start_listening(lambda data: ())
            's.speak(\'Start\')
            'if DEBUG:
            '\ttimedlog(\"Starting\")
            'CONTROLLER.run()\n\n\n\n
            '";
        }


    }
    return intercalate("\n", retVal);
}



list[str] generateTrigger(DefInfo defInfo) {
    if (ct <- defInfo.colorTrigger) {
        cs_selected = "";
        if(ct.sensor == "left") cs_selected = "CS_L";
        if(ct.sensor == "right") cs_selected = "CS_R";
        if(ct.sensor == "mid") cs_selected = "CS_M";
        return ["read_color_sensor(<cs_selected>) == \"<ct.color>\""];
    }
    if (dt <- defInfo.distanceTrigger) {
        if(dt.sensor == "front") return ["readings_dict[\"ULT_F\"] \< <dt.distance>"];
        if(dt.sensor == "back") return ["read_ultrasonic_sensor(ULT_B) \< <dt.distance>"];
    }
    if (tt <- defInfo.touchTrigger) {
        if(tt.sensor == "left") return ["readings_dict[TOUCH_L]"];
        if(tt.sensor == "right") return ["readings_dict[TOUCH_R]"];
        if(tt.sensor == "back") return ["readings_dict[TOUCH_B]"];
        if(tt.sensor == "any") return ["readings_dict[TOUCH_L] or readings_dict[TOUCH_R] or readings_dict[TOUCH_B]"];
    }
    return ["False"];
}

list[str] generateAction(DefInfo defInfo) {
    if (ma <- defInfo.moveAction) {
        if(ma.direction == "forward") return ["MOTOR.run(forward=True, distance=<ma.distance>, speed=<ma.speed>)"];
        if(ma.direction == "backward") return ["MOTOR.run(forward=False, distance=<ma.distance>, speed=<ma.speed>)"];
        if(ma.direction == "stop") return ["MOTOR.stop()"];
    }
    if (ta <- defInfo.turnAction) {
        if(ta.direction == "left") return ["MOTOR.turn(direction=\"LEFT\", degrees=<ta.angle>, speed=<ta.speed>)"];
        if(ta.direction == "right") return ["MOTOR.turn(direction=\"RIGHT\", degrees=<ta.angle>, speed=<ta.speed>)"];
        if(ta.direction == "none") return ["MOTOR.turn(direction=\"None\", degrees=<ta.angle>, speed=<ta.speed>)"];
    }
    if (sa <- defInfo.speakAction) {
        if (sa.text == "&.&.&.") return ["S.beep()"];
        return ["S.speak(\"<sa.text>\")"];
    }
    if (la <- defInfo.ledAction) {
        return ["set_led(LEDS, \"<toUpperCase(la.color)>\")"];
    }
    if (msa <- defInfo.measureAction) {
        return ["ARM_MOTOR.move(up=False, rotations=1, block=True)", "time.sleep(<msa.time>)", "ARM_MOTOR.move(up=True, rotations=1, block=True)"];
    }
    return ["()"];
}




tuple[list[str], map[str, list[str]]] extractComponentFromId(tm, startIdSrc, map[str, list[str]] ret_map, list[str](DefInfo) generator_method) {
    retVal = [];
    component_str = getContent(startIdSrc);

    if (component_str in ret_map) {
        retVal += ret_map[component_str];
        return <retVal, ret_map>;
    }
    DefInfo defInfo = findReferenceFromSrc(tm, startIdSrc);
    if (l <- defInfo.idList) {
        for (idSrc <- l.idList) {
            tmp_ret = extractComponentFromId(tm, idSrc, ret_map, generator_method);
            retVal += tmp_ret[0];
            ret_map = tmp_ret[1];
        }
    }
    else retVal += generator_method(defInfo);

    ret_map += (component_str: retVal);
    return <retVal, ret_map>;
}

// tuple[list[str], map[str, list[str]]] extractActionFromId(tm, startIdSrc, map[str, list[str]] action_map) {
//     retVal = [];
//     action_str = getContent(startIdSrc);

//     if (action_str in action_map) {
//         retVal += action_map[action_str];
//         return <retVal, action_map>;
//     }
//     DefInfo defInfo = findReferenceFromSrc(tm, startIdSrc);
//     if (l <- defInfo.idList) {
//         for (idSrc <- l.idList) {
//             tmp_ret = extractActionFromId(tm, idSrc, action_map);
//             retVal += tmp_ret[0];
//             action_map = tmp_ret[1];
//         }
//     }
//     else retVal += generateAction(defInfo);

//     action_map += (action_str: retVal);
//     return <retVal, action_map>;
// }

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

