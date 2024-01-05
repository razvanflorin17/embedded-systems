module Generator

import IO;
import Set;
import List;
import String;
import Location;
import Set;
import Map;
import util::Math;

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
        action_map = tmp_ret[2];

        retVal = "
        '
        '<mac>
        '
        '<bhv_list>
        '
        '<bhv_def>
        '
        '
        '<generateMissionsDef(missions, tm, trigger_map, action_map)>
        '
        '
        '<printMissionsUsage(missions, tm)>
        '";

    }
    // retValTmp = [];
    // for (<tl> <- {<taskList> | /(TaskList) `<TaskList taskList>` := cst}) {
    //     retValTmp += "<printTaskList(tl)>";
    // }

    


    return retVal;

}

list[loc] extractBhvs(missions, tm) {
    bhvs = ();
    for (<mission> <- [<id> |/(ID) `<ID id>` := missions]) {
        DefInfo defInfo = findReference(tm, mission);
        if (miss <- defInfo.mission) {
            for (behavior <- miss.behaviorList) {
                if(getContent(behavior) notin bhvs) {
                    bhvs += (getContent(behavior): behavior);
                }
                
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

tuple[str, map[str, list[DefInfo]], map[str, list[DefInfo]]] generateBhvsDef(list[loc] bhv_list, tm) {
    trigger_map = ();
    action_map = ();
    retVal = [];
    for (bhvSrc <- bhv_list) {
        DefInfo defInfo = findReferenceFromSrc(tm, bhvSrc);
        bhv_str = getContent(bhvSrc);
        if (bhv <- defInfo.behavior) {
            
            trigger_list = [];
            for (trigger <- bhv.triggerList) {
                tmp_ret = extractComponentFromId(tm, trigger, trigger_map);
                trigger_list += generateFromDefInfo(tmp_ret[0], generateTrigger);
                trigger_map = tmp_ret[1];
            }
            action_list = [];
            for (action <- bhv.actionList) {
                tmp_ret = extractComponentFromId(tm, action, action_map);
                action_list += generateFromDefInfo(tmp_ret[0], generateAction);
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
    return <intercalate("\n\n\n", retVal), trigger_map, action_map>;
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


str generateMissionsDef(missions, tm, trigger_map, action_map) {
    retVal = [];
    mission_set = ();
    for (<mission> <- {<id> |/(ID) `<ID id>` := missions}) {
        if ("<mission>" notin mission_set) {
            mission_set += ("<mission>": mission);
        }
    }
    mission_list = [mission_set[miss] | miss <- mission_set];  
    for (mission <- mission_list) {
        DefInfo defInfo = findReference(tm, mission);
        if (miss <- defInfo.mission) {
            task_list = [];
            for (task <- miss.taskList) {
                task_items = [];
                if (task.activityType == "TRIGGER") {
                    for (trigger <- task.activityList) {
                        tmp_ret = extractComponentFromId(tm, trigger, trigger_map);
                        trigger_map = tmp_ret[1];
                        task_items += generateFromDefInfo(tmp_ret[0], generateTrigger);
                    }
                    if (task.activityListMod != "ALLORD")   task_items = toList(toSet(task_items));
                }
                else if (task.activityType == "ACTION") {
                    for (action <- task.activityList) {
                        tmp_ret = extractComponentFromId(tm, action, action_map);
                        action_map = tmp_ret[1];
                        task_items += tmp_ret[0];
                    }
                }
                task_list += <task_items, task.activityType, task.activityListMod>;

            }
            retVal += "<printMissionTaskBhv(task_list, "<mission>")>";
            retVal += "<miss>";
        }
    }
    return intercalate("\n\n", retVal);
}

str printMissionTaskBhv(list[tuple[list[value], str, str]] task_list, mission_name) {
    
    list[str] states_init_reg = [];
    list[str] states_init_conds = [];
    list[int] action_states_index = [];
    list[list[DefInfo]] action_task_list = [];
    int state_cont = 0;


    for (task <- task_list) {
        list[value] task_items = task[0];
        task_type = task[1];
        task_list_mod = task[2];

        if (task_type == "TRIGGER") {
            if (task_list_mod == "ANY" || task_list_mod == "SIM") {
                states_init_conds += "[lambda: <printTriggers(task_items, task_list_mod)>]";
                states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", 1)";
                state_cont += 1;
            }
            else if (task_list_mod == "ALL") {
                states_init_conds += "<printListLambda(task_items)>";
                states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", <size(task_items)>)";
                state_cont += 1;
            }
            else {
                for (trigger <- task_items) {
                    states_init_conds += "[lambda: <trigger>]";
                    states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", 1)";
                    state_cont += 1;
                }
            }
        }
        else if (task_type == "ACTION") {
            states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", 1)";
            states_init_conds += "[lambda: RUNNING_ACTIONS_DONE]";
            action_task_list += [task_items];
            action_states_index += state_cont;
            state_cont += 1;
        }
    }

    list[str] states_init = states_init_reg + "self.task_list_cond = [<intercalate(", ", states_init_conds)>]";
    states_check = "for i in range(len(self.task_list_cond[EXECUTING_STATE])):
    '\tTASK_REGISTRY.update(\"state_\" + str(EXECUTING_STATE), self.task_list_cond[EXECUTING_STATE][i](), i)
    'if TASK_REGISTRY.task_done(\"state_\" + str(EXECUTING_STATE)):
    '\tEXECUTING_STATE += 1
    '\tRUNNING_ACTIONS_DONE = False
    '";

    retVal = "
    'class <mission_name>_updateTasksBhv(Behavior):
    '\tdef __init__(self):
    '\t\tBehavior.__init__(self)
    '\t\tglobal EXECUTING_STATE
    '\t\tEXECUTING_STATE = 0
    '\t\tself.fired = False
    '\t\t<intercalate("\n", states_init)>
    '
    '\tdef check(self):
    '\t\tglobal EXECUTING_STATE, RUNNING_ACTIONS_DONE
    '\t\tif not self.fired:
    '\t\t\t<states_check>
    '\t\t\tif EXECUTING_STATE == <state_cont>:
    '\t\t\t\tself.fired = True
    '\t\t\t\treturn True
    '\t\treturn False
    '
    '\tdef action(self):
    '\t\treturn True
    '
    '\tdef suppress(self):
    '\t\tpass
    '
    '";
    retVal +=  printMissionRunningBhv(action_task_list, action_states_index, state_cont, mission_name) + "\n\n";
    return retVal;
}

str printMissionRunningBhv(list[list[DefInfo]] action_task, list[int] action_states_index, int max_state_index, mission_name) {
    list[str] operations_init = [];
    list[str] log_operations_init = [];
    int j = 0;
    for (int i <- [0 .. max_state_index]) {
        if (i in action_states_index) {
            operations_init += printListLambda(generateActionTask(action_task[j]));
            j += 1;
        }
        else {
            operations_init += printListLambda(["MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3)", "(self.counter_action := 0)"]);
        }
    }


    action_update = "
    'for operation in self.operations[EXECUTING_STATE][self.counter_action:]:
    '\toperation()
    '\twhile self.motor.is_running and not self.supressed:
    '\t\tpass
    '\tif not self.supressed:
    '\t\tself.counter_action += 1
    '
    'if self.counter_action == len(self.operations[EXECUTING_STATE]):
    '\tRUNNING_ACTIONS_DONE = True
    '\tself.counter_action = 0
    '\treturn True
    'return False
    '";
    
    retVal = "
    'class <mission_name>_RunningBhv(Behavior):
    '\tdef __init__(self):
    '\t\tBehavior.__init__(self)
    '\t\tglobal RUNNING_ACTIONS_DONE
    '\t\tself.counter_action = 0
    '\t\tRUNNING_ACTIONS_DONE = False
    '\t\tself.operations = [<intercalate(", ", operations_init)>]
    '
    '\tdef check(self):
    '\t\tglobal RUNNING_ACTIONS_DONE
    '\t\treturn not TASK_REGISTRY.tasks_done() and not RUNNING_ACTIONS_DONE
    '
    '\tdef action(self):
    '\t\t<action_update>
    '
    '\tdef suppress(self):
    '\t\tself.motor.stop()
    '\t\tself.supressed = True
    '\t\tif DEBUG:
    '\t\t\ttimedlog(\"RunningBhv suppressed\")
    '\t\tpass
    '";
    
    return retVal;
}


str printMissionsUsage(missions, tm) {
    retVal = [];
    for (<mission> <- [<id> |/(ID) `<ID id>` := missions]) {
        DefInfo defInfo = findReference(tm, mission);
        if (miss <- defInfo.mission) {
            retVal += "CONTROLLER = Controller(return_when_no_action=True)
            'TASK_REGISTRY = TaskRegistry()
            'CONTROLLER.add(<mission>_updateTasksBhv())
            '";

            list[str] feedback_start_operations = [];
            list[str] feedback_end_operations = [];
            for (feedback_operation_src <- miss.feedbacks[0]) {
                DefInfo feedback_operation = findReferenceFromSrc(tm, feedback_operation_src);
                // feedback_start_operations += "<feedback_operation>";
                feedback_start_operations += generateActionFeedback(feedback_operation);

            }
            for (feedback_operation_src <- miss.feedbacks[1]) {
                DefInfo feedback_operation = findReferenceFromSrc(tm, feedback_operation_src);
                // feedback_end_operations += "<feedback_operation>";
                feedback_end_operations += generateActionFeedback(feedback_operation);
            }


            for (behavior <- miss.behaviorList) {
                retVal += "CONTROLLER.add(<getContent(behavior)>_bhv())";
            }
            retVal += "bluetooth_connection.start_listening(lambda data: ())
            's.speak(\'Start\') # REMOVE BEFORE DELIVERY
            '
            'for operation in <printListLambda(feedback_start_operations)>:
            '\toperation()
            '
            'if DEBUG:
            '\ttimedlog(\"Starting\")
            'CONTROLLER.run()
            '
            '
            'for operation in <printListLambda(feedback_end_operations)>:
            '\toperation()
            '\n\n\n
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
        return ["S.speak(\"<sa.text>\", play_type=S.PLAY_NO_WAIT_FOR_COMPLETE)"];
    }
    if (la <- defInfo.ledAction) {
        return ["set_led(LEDS, \"<toUpperCase(la.color)>\")"];
    }
    if (msa <- defInfo.measureAction) {
        return ["ARM_MOTOR.move(up=False, rotations=1, block=True)", "time.sleep(<msa.time>)", "ARM_MOTOR.move(up=True, rotations=1, block=True)"];
    }
    return ["()"];
}

list[str] generateActionFeedback(DefInfo action_defInfo) {
    if (sa <- action_defInfo.speakAction) {
        if (sa.text == "&.&.&.") return ["S.beep()"];
        return ["S.speak(<sa.text>, play_type=S.PLAY_WAIT_FOR_COMPLETE)"];
    }
    if (la <- action_defInfo.ledAction) {
        return ["feedback_leds_blocking(LEDS, \"<toUpperCase(la.color)>\")"];
    }
    return ["()"];
}


list[str] generateActionTask(list[DefInfo] actions_defInfo) {
    operations = [];
    int i = 0;
    while (i < size(actions_defInfo)) {
        if (ma_i <- actions_defInfo[i].moveAction || ta_i <- actions_defInfo[i].turnAction) {
            if (ma <- actions_defInfo[i].moveAction && ma.direction == "stop") operations += ["MOTOR.stop()"];
            else {
                actions_to_compute = [];
                for(int j <- [i .. size(actions_defInfo)]) {
                    if (ma_j <- actions_defInfo[j].moveAction) {
                        if (ma_j.direction == "stop") break;
                        else actions_to_compute += actions_defInfo[j];
                    }
                    else if (ta_j <- actions_defInfo[j].turnAction) actions_to_compute += actions_defInfo[j];
                    else break;
                    i += 1;
                }
                operations += ["MOTOR.oddometry_start()"];
                for (coordinates <- computeCoordinates(actions_to_compute)) {
                    operations += ["MOTOR.to_coordinates(<coordinates[0]>, <coordinates[1]>, speed=<coordinates[2]>)"];
                }
                operations += ["MOTOR.oddometry_stop()"];
            }
        }
        else {
            operations += generateAction(actions_defInfo[i]);
            i += 1;
        }
    }
    return operations;
}


list[tuple[int, int, int]] computeCoordinates(list[DefInfo] actions) {
    int angle = 90;
    real x = 0.0;
    real y = 0.0;
    int speed = 0;
    retVal = [];
    curr_action = "";
    if (ta <- actions[0].turnAction) last_action = "turn";
    else last_action = "move";

    for (action <- actions) {
        if (ta <- action.turnAction) {
            if (ta.direction == "left") angle = (angle + ta.angle) %360;
            if (ta.direction == "right" || ta.direction == "none") angle = (angle - ta.angle) %360;
            speed = ta.speed;
            curr_action = "turn";
        }
        else if (ma <- action.moveAction) {
            d = 0;
            if (ma.direction == "forward") d += ma.distance;
            if (ma.direction == "backward") d -= ma.distance;
            x += d * cos(angle * PI()/180);
            y += d * sin(angle * PI()/180);
            curr_action = "move";
            speed = ma.speed;
        }

        if (curr_action != last_action) {
            retVal += [<toInt(x), toInt(y), speed>];
            last_action = curr_action;
        }

    }
    return retVal;
}


// tuple[list[str], list[str]] generateActionTask(DefInfo defInfo) {
//     operations = [];
//     log_operations = [];
//     if (ma <- defInfo.moveAction) {
//         if (ma.direction == "stop") return <["MOTOR.stop()"], ["()"]>;
//         else {
//             base_distance = 30;
//             for (int i <- [0, base_distance .. ma.distance]) {
//                 distance = min(base_distance, ma.distance - i);
//                 if (ma.direction == "forward") operations += ["MOTOR.run(forward=True, distance=<distance>, speed=<ma.speed>)"];
//                 if (ma.direction == "backward") operations += ["MOTOR.run(forward=False, distance=<distance>, speed=<ma.speed>)"];
//                 log_operations += "MOTOR.log_distance(<distance>)";
//             }
//             return <operations, log_operations>;
//         }
//     }
//     if (ta <- defInfo.turnAction) {
//         base_angle = 30;
//         for (int i <- [0, base_angle .. ta.angle]) {
//             angle = min(base_angle, ta.angle - i);
//             if (ta.direction == "left") operations += ["MOTOR.turn(direction=\"LEFT\", degrees=<angle>, speed=<ta.speed>)"];
//             if (ta.direction == "right") operations += ["MOTOR.turn(direction=\"RIGHT\", degrees=<angle>, speed=<ta.speed>)"];
//             if (ta.direction == "none") operations += ["MOTOR.turn(direction=\"None\", degrees=<angle>, speed=<ta.speed>)"];
//             log_operations += "MOTOR.log_angle(<angle>)";
//         }
//         return <operations, log_operations>;
//     }
//     operations += generateAction(defInfo);
//     return <operations, ["()" | i <- [0 .. size(operations)]]>;
// }


list[str] generateFromDefInfo(list[DefInfo] defInfoList, list[str](DefInfo) generator_method) {
    retVal = [];
    for (defInfo <- defInfoList) {
        retVal += generator_method(defInfo);
    }
    return retVal;
}


tuple[list[DefInfo], map[str, list[DefInfo]]] extractComponentFromId(tm, startIdSrc, map[str, list[DefInfo]] ret_map) {
    retVal = [];
    component_str = getContent(startIdSrc);

    if (component_str in ret_map) {
        retVal += ret_map[component_str];
        return <retVal, ret_map>;
    }
    DefInfo defInfo = findReferenceFromSrc(tm, startIdSrc);
    if (l <- defInfo.idList) {
        for (idSrc <- l.idList) {
            tmp_ret = extractComponentFromId(tm, idSrc, ret_map);
            retVal += tmp_ret[0];
            ret_map = tmp_ret[1];
        }
    }
    else retVal += defInfo;

    ret_map += (component_str: retVal);
    return <retVal, ret_map>;
}


int min(int a, int b) {
    if (a < b) return a;
    return b;
}