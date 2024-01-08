module Generator

import Static_Generator;

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
    static_code = static_code_generator();
    rVal = generator(cst, static_code[0], static_code[1], static_code[2]);
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

tuple[str, str] generator(cst, str static_code, tuple[str, str] master_bhvs, str slave_code) { // WIP
    str retVal = static_code;
    str master_ret = "";
    str slave_ret = "";

    if(/(RoverConfig) `Rover: <IDList missions> MAC: <STR mac>` := cst) {
        
        master_ret += generator_master(cst, missions, "<mac>", master_bhvs);
        slave_ret += generator_slave("<mac>", slave_code);

    }
    // retValTmp = [];
    // for (<tl> <- {<taskList> | /(TaskList) `<TaskList taskList>` := cst}) {
    //     retValTmp += "<printTaskList(tl)>";
    // }

    master_ret = retVal + master_ret;
    slave_ret = retVal + slave_ret;


    return <master_ret, slave_ret>;
}

str generator_slave(str master_mac, str slave_code) {
    return "";
}

str generator_master(cst, missions, str master_mac, tuple[str, str] master_bhvs) {
    str retVal = "";
    trigger_list = [];
    action_list = [];
    tm = modulesTModelFromTree(cst);

    bhv_list = extractBhvs(missions, tm);
    tmp_ret = generateBhvsDef(bhv_list, tm);
    bhv_def = tmp_ret[0];
    trigger_map = tmp_ret[1];
    action_map = tmp_ret[2];

    retVal += "
    '<master_mac>
    '
    '
    '
    '<bhv_def>
    '
    '
    '<generateMissionsDef(missions, tm, trigger_map, action_map)>
    '
    '
    '<printMissionsUsage(missions, tm, master_bhvs)>
    '";

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
                states_init += "self.counter_conds = 0";
                states_init += "self.trigger_list = <printListLambda(trigger_list)>";
                states_init += "self.firing = False";
                states_init += "self.to_fire = False";
                states_check += "if not self.to_fire and not self.firing:
                '\tif self.trigger_list[self.counter_conds]():
                '\t\tself.counter_conds += 1
                '\t\tself.to_fire = (self.counter_conds == <size(trigger_list)>)
                '";

            }
            else {
                trigger_list = toList(toSet(trigger_list));
                states_init += "self.firing = False";
                states_init += "self.to_fire = False";
                states_check += "if not self.to_fire and not self.firing:
                '\tself.to_fire = (<printTriggers(trigger_list, bhv.triggerListMod)>)
                '";
            }

            states_check += "\tif self.to_fire:
            '\t\tself.operations = <printListLambda(action_list)>
            'return self.to_fire and not self.firing
            '";
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
    '\t\tself.suppressed = False
    '\t\tself.operations = []
    '\t\t<states_init>
    '
    '
    '\tdef _reset(self):
    '\t\tself.operations = []
    '\t\tMOTOR.stop()
    '\t\t<states_init>
    '
    '
    '\tdef check(self):
    '\t\t<states_check>
    '
    '
    '\tdef action(self):
    '\t\tglobal OVERRIDED_LAKE, MEASURE_OBJ
    '\t\tself.suppressed = False
    '\t\tself.firing = True
    '\t\tself.to_fire = False
    '\t\tif DEBUG:
    '\t\t\ttimedlog(\"<bhv_str> fired\")
    '
    '\t\tfor operation in self.operations:
    '\t\t\toperation()
    '\t\t\twhile MOTOR.is_running and not self.suppressed:
    '\t\t\t\tpass
    '\t\t\tif self.suppressed:
    '\t\t\t\tbreak
    '
    '\t\tself._reset()
    '
    '\t\tif DEBUG and not self.suppressed:
    '\t\t\ttimedlog(\"<bhv_str> done\")
    '\t\treturn not self.suppressed
    '
    '
    '\tdef suppress(self):
    '\t\tMOTOR.stop()
    '\t\tself.suppressed = True
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
            list[str] feedback_timeout_operations = [];

            for (feedback_operation_src <- miss.feedbacks[2]) {
                DefInfo feedback_operation = findReferenceFromSrc(tm, feedback_operation_src);
                feedback_timeout_operations += generateActionFeedback(feedback_operation);
            }
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
                task_list += <task_items, task.activityType, task.activityListMod, task.timeout>;

            }
            if (isEmpty(feedback_timeout_operations)) feedback_timeout_operations += ["S.speak(\"Mission <mission> timeouted\")"];
            retVal += "<printMissionControllerBhvDef(task_list, "<mission>", feedback_timeout_operations)>";
        }
    }
    return intercalate("\n\n", retVal);
}


str printMissionControllerBhvDef(list[tuple[list[value], str, str, int]] task_list, mission_name, list[str] timeout_operations) {
    
    list[str] states_init_reg = [];
    list[str] states_init_conds = [];
    list[int] action_states_index = [];
    list[int] states_timeout = [];
    list[str] operations_init = [];
    list[list[DefInfo]] action_task_list = [];
    int state_cont = 0;


    for (task <- task_list) {
        list[value] task_items = task[0];
        task_type = task[1];
        task_list_mod = task[2];
        int task_timeout = task[3];

        if (task_type == "TRIGGER") {
            if (task_list_mod == "ANY" || task_list_mod == "SIM") {
                states_init_conds += "[lambda: <printTriggers(task_items, task_list_mod)>]";
                states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", 1)";
                states_timeout += task_timeout;
                state_cont += 1;
            }
            else if (task_list_mod == "ALL") {
                states_init_conds += "<printListLambda(task_items)>";
                states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", <size(task_items)>)";
                states_timeout += task_timeout;
                state_cont += 1;
            }
            else {
                prev_state_cont = state_cont;
                for (trigger <- task_items) {
                    states_init_conds += "[lambda: <trigger>]";
                    states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", 1)";
                    state_cont += 1;
                }
                for (int i <- [prev_state_cont .. state_cont]) {
                    states_timeout += toInt(task_timeout / (state_cont - prev_state_cont));
                }
            }
            operations_init += printListLambda(["MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3)", "self._caction_dec()"]);
        }
        else if (task_type == "ACTION") {
            states_init_reg += "TASK_REGISTRY.add(\"state_<state_cont>\", 1)";
            states_init_conds += "[lambda: self.running_actions_done]";
            operations_init += printListLambda(generateActionTask(task_items));
            states_timeout += task_timeout;
            state_cont += 1;

        }
    }

    list[str] states_init = states_init_reg + "self.task_list_cond = [<intercalate(", ", states_init_conds)>]" + "self.timeout = [<intercalate(", ", states_timeout)>]" + "self.operations = [<intercalate(", ", operations_init)>]";
    
    states_check = "for i in range(len(self.task_list_cond[self.executing_state])):
    '\tTASK_REGISTRY.update(\"state_\" + str(self.executing_state), self.task_list_cond[self.executing_state][i](), i)
    '
    'if TASK_REGISTRY.task_done(\"state_\" + str(self.executing_state)):
    '\tself.suppress()
    '\tself.executing_state += 1
    '\tself.counter_action = 0
    '\tself.running_actions_done = False
    '\tself.timer = 0
    '\treturn self.executing_state \< <state_cont>
    '";

    timer_check = "if self.timer == 0:
    '\tself.timer = time.time()
    'else:
    '\tself.timeouted = (time.time() - self.timer) \> self.timeout[self.executing_state]
    '\tif self.timeouted:
    '\t\tself.suppress()
    '\t\tTASK_REGISTRY.set_all(\"state_\" + str(self.executing_state), 1)
    '\t\tself.executing_state += 1
    '\t\tself.running_actions_done = False
    '\t\tself.timer = 0
    '\t\treturn True
    '";

    action_update = "for operation in self.operations[self.executing_state][self.counter_action:]:
    '\toperation()
    '\twhile MOTOR.is_running and not self.suppressed and not TASK_REGISTRY.task_done(\"state_\" + str(self.executing_state)):
    '\t\tpass
    '\tif self.suppressed:
    '\t\tbreak
    '\telse:
    '\t\tself.counter_action += 1
    '
    'if not self.suppressed and self.counter_action == len(self.operations[self.executing_state]):
    '\tself.running_actions_done = True
    '\tself.counter_action = 0
    '";

    timeout_execution = "MOTOR.stop()
    'if DEBUG:
    '\ttimedlog(\"<mission_name> timeouted, at state\" + str(self.executing_state - 1))
    'for operation in <printListLambda(timeout_operations)>:
    '\toperation()
    'self.timeouted = False
    'return True
    '";

    retVal = "
    'class <mission_name>_controllerBhv(Behavior):
    '\tdef __init__(self):
    '\t\tBehavior.__init__(self)
    '\t\tself.executing_state = 0
    '\t\tself.counter_action = 0
    '\t\tself.running_actions_done = False
    '\t\tself.fired = False
    '\t\tself.timer = 0
    '\t\tself.timeouted = False
    '\t\t<intercalate("\n", states_init)>
    '
    '\tdef check(self):
    '\t\tif self.timeouted:
    '\t\t\treturn True
    '\t\tif TASK_REGISTRY.all_tasks_done():
    '\t\t\treturn False
    '
    '\t\t<timer_check>
    '
    '\t\t<states_check>
    '\t\treturn not self.fired
    '
    '\tdef action(self):
    '\t\tglobal OVERRIDED_LAKE, MEASURE_OBJ, MEASURE_LAKE
    '\t\tif self.timeouted:
    '\t\t\t<timeout_execution>
    '\t\tself.suppressed = False
    '\t\tself.fired = True
    '\t\t<action_update>
    '\t\tself.fired = False
    '\t\treturn not self.suppressed
    '
    '\tdef _caction_dec(self, cond=True):
    '\t\tif cond:
    '\t\t\tself.counter_action = self.counter_action - 2
    '
    '\tdef suppress(self):
    '\t\tMOTOR.stop()
    '\t\tself.suppressed = True
    '\t\tif DEBUG:
    '\t\t\ttimedlog(\"RunningBhv suppressed\")
    '
    '";
    return retVal;
}

str printMissionsUsage(missions, tm, tuple[str, str] master_bhvs) {
    retVal = [];
    for (<mission> <- [<id> |/(ID) `<ID id>` := missions]) {
        DefInfo defInfo = findReference(tm, mission);
        if (miss <- defInfo.mission) {
            retVal += "CONTROLLER = Controller(return_when_no_action=True)
            'TASK_REGISTRY = TaskRegistry()
            '";

            list[str] feedback_start_operations = [];
            list[str] feedback_end_operations = [];
            for (feedback_operation_src <- miss.feedbacks[0]) {
                DefInfo feedback_operation = findReferenceFromSrc(tm, feedback_operation_src);
                feedback_start_operations += generateActionFeedback(feedback_operation);

            }
            if (isEmpty(feedback_start_operations)) feedback_start_operations += ["S.speak(\"Starting mission <mission>\")"];
            for (feedback_operation_src <- miss.feedbacks[1]) {
                DefInfo feedback_operation = findReferenceFromSrc(tm, feedback_operation_src);
                feedback_end_operations += generateActionFeedback(feedback_operation);
            }
            if (isEmpty(feedback_end_operations)) feedback_end_operations += ["S.speak(\"Mission <mission> done\")"];
            retVal += master_bhvs[0];
            for (behavior <- miss.behaviorList) {
                retVal += "CONTROLLER.add(<getContent(behavior)>_bhv())";
            }
            retVal += master_bhvs[1];
            retVal += "CONTROLLER.add(<mission>_controllerBhv())";
            retVal += "#BLUETOOTH_CONNECTION.start_listening(lambda data: ())
            'S.speak(\'Start\') # REMOVE BEFORE DELIVERY
            '
            'for operation in <printListLambda(feedback_start_operations)>:
            '\toperation()
            '
            'if DEBUG:
            '\ttimedlog(\"Starting <mission>\")
            'CONTROLLER.start()
            '
            '
            'for operation in <printListLambda(feedback_end_operations)>:
            '\toperation()
            '
            'if DEBUG:
            '\ttimedlog(\"Done <mission>\")
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
        return ["READINGS_DICT[\"<cs_selected>\"] == \"<ct.color>\""];
    }
    if (dt <- defInfo.distanceTrigger) {
        if(dt.sensor == "front") return ["READINGS_DICT[\"ULT_F\"] \< <dt.distance>"];
        if(dt.sensor == "back") return ["READINGS_DICT[\"ULT_B\"] \< <dt.distance>"];
    }
    if (tt <- defInfo.touchTrigger) {
        if(tt.sensor == "left") return ["READINGS_DICT[\"TS_L\"]"];
        if(tt.sensor == "right") return ["READINGS_DICT[\"TS_R\"]"];
        if(tt.sensor == "back") return ["READINGS_DICT[\"TS_B\"]"];
        if(tt.sensor == "any") return ["READINGS_DICT[\"TS_L\"] or READINGS_DICT[\"TS_R\"] or READINGS_DICT[\"TS_B\"]"];
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
        return ["S.speak(<sa.text>, play_type=S.PLAY_NO_WAIT_FOR_COMPLETE)"];
    }
    if (la <- defInfo.ledAction) {
        return ["set_led(LEDS, \"<toUpperCase(la.color)>\")"];
    }
    if (msa <- defInfo.measureAction) {
        if (msa.target == "object") return ["(MEASURE_OBJ := True)", "ARM.move(up=False, rotations=0.5, block=True)", "time.sleep(<msa.time>)", "ARM.move(up=True, rotations=0.5, block=True)", "(MEASURE_OBJ := False)"];
        else return ["(OVERRIDED_LAKE := True)", "measure_lake(motor=MOTOR, left=READINGS_DICT[\"CS_L\"] == \"<msa.target>\", right=READINGS_DICT[\"CS_R\"] == \"<msa.target>\", mid=READINGS_DICT[\"CS_M\"] == \"<msa.target>\", sleep_time = <msa.time>, bhv=self)", "(OVERRIDED_LAKE := False)"];
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
                operations += ["MOTOR.odometry_start()"];
                for (coordinates <- computeCoordinates(actions_to_compute)) {
                    operations += ["MOTOR.to_coordinates(<coordinates[0]>, <coordinates[1]>, speed=<coordinates[2]>, random_rep=True, bhv=self)"];
                }
                operations += ["MOTOR.odometry_stop()"];
            }
        }
        else if (msa <- actions_defInfo[i].measureAction) {
            if (msa.target == "object") operations += ["(MEASURE_OBJ := True)", "ARM.move(up=False, rotations=0.5, block=True)", "time.sleep(<msa.time>)", "ARM.move(up=True, rotations=0.5, block=True)", "(MEASURE_OBJ := False)"];
            else operations += ["(MEASURE_LAKE := (<msa.target>, <msa.time>))", "MOTOR.run(forward=True, distance=100, brake=False, speedM=1.3)", "self._caction_dec(cond=(not MEASURE_LAKE))"];
            i += 1;
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
    last_action = "";

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
            if (curr_action != "turn") retVal += [<toInt(x), toInt(y), speed>];
            last_action = curr_action;
        }

    }
    return retVal;
}

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