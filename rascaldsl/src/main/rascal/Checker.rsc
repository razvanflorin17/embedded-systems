module Checker

import Syntax;
 
extend analysis::typepal::TypePal;
import ParseTree;
import String;


public TModel modulesTModelFromTree(Tree pt) {
    if (pt has top) pt = pt.top;
    TypePalConfig a = getModulesConfig();
    c = newCollector("collectAndSolve", pt, a);
    collect(pt, c);
    return newSolver(pt, c.run()).run();
}

// typepal adt overload

data IdRole 
     = triggerId()
     | actionId()
     | behaviorId()
     | missionId()
;

data AType 
     = idListType()
     | distanceTriggerType()
     | colorTriggerType()
     | touchTriggerType()
     | moveActionType()
     | turnActionType()
     | speakActionType()
     | ledActionType()
     | behaviorType()
     | missionType()
;

// ADT definitions

data ColorTrigger = colorTrigger(str sensor = "", str color = "");
data DistanceTrigger = distanceTrigger(str sensor = "", int distance = 0);
data TouchTrigger = touchTrigger(str sensor = "");

data IDList = idList(list[loc] idList = []);

data MoveAction = moveAction(str direction = "", int distance = 0);
data TurnAction = turnAction(int angle = 0);
data SpeakAction = speakAction(str text = "");
data LedAction = ledAction(str color = "");

data Behavior = behavior(list[loc] triggerList = [], list[loc] actionList = [], str triggerListMod="ALL");
data Mission = mission(list[loc] taskList = [], list[loc] behaviorList = [], str taskListMod="ALL");


// ADT constructors

data DefInfo(list[ColorTrigger] colorTrigger = []);
data DefInfo(list[DistanceTrigger] distanceTrigger = []);
data DefInfo(list[TouchTrigger] touchTrigger = []);

data DefInfo(list[IDList] idList = []);

data DefInfo(list[MoveAction] moveAction = []);
data DefInfo(list[TurnAction] turnAction = []);
data DefInfo(list[SpeakAction] speakAction = []);
data DefInfo(list[LedAction] ledAction = []);

data DefInfo(list[Behavior] behavior = []);
data DefInfo(list[Mission] mission = []);

//   TypePalConfig

Accept isAcceptableSimple(loc def, Use use, Solver s) {
     if (def.offset > use.occ.offset) {return ignoreSkipPath();}
     return acceptBinding();
}



bool idMayOverload (set[loc] defs, map[loc, Define] defines) { //code for uniques ids
    roles = {defines[def].idRole | def <- defs};
    return roles == {};
}

private TypePalConfig getModulesConfig() = tconfig(
     verbose=true,
     logTModel = true,
     logAttempts = true,
     logSolverIterations= true,
     logSolverSteps = true, 
     isSubType = subtype,
     // triggerGetTypeNamesAndRole = triggerGetTypeNamesAndRole,
     // actionGetTypeNamesAndRole = actionGetTypeNamesAndRole,
     isAcceptableSimple = isAcceptableSimple,
     idMayOverload = idMayOverload
);

// helper methods

void checkIdList(current, Solver s, idCheckList, list[AType] validTypes, list[str] excludedIds) {
     for (<id> <- {<id> |/(ID) `<ID id>` := idCheckList}) {
          s.requireFalse(("<id>" in excludedIds), error(id, "%v is excluded", "<id>"));
          s.requireTrue((s.getType(id) in validTypes), error(id,  "type should be one of %v, instead of %t", validTypes, id));
     }
}

list[loc] collectIdList(Collector c, idCollectList, role) {
     result = [];
     for (<id> <- {<id> |/(ID) `<ID id>` := idCollectList}) {
          result +=  id.src;
          c.use(id, {role});
     }
     return result;
}

// typepal collectors

void collect(current: (IDList)`<IDList idlist>`, Collector c) {
     c.fact(idlist, idListType());
}

//  Trigger

void collect(current: (RoverTrigger) `COLOR <ColorSensor colorSensor> <ColorReadable color>`, Collector c) {
     c.fact(current, colorTriggerType());
}

void collect(current: (RoverTrigger) `INDISTANCE <DistanceSensor distanceSensor> <NATURAL distance>`, Collector c) {
     c.fact(current, distanceTriggerType());
}

void collect(current: (RoverTrigger) `TOUCH <TouchSensor touchSensor>`, Collector c) {
     c.fact(current, touchTriggerType());
}

//DEFINITION
void collect(current: (Trigger) `<ID idNew> <TriggerAssignment triggerAssignment> <RoverTrigger roverTrigger>`,  Collector c) {
     if(/(ColorTrigger)`COLOR <ColorSensor colorSensor> <ColorReadable color>` := roverTrigger) {
          dt = defType(colorTriggerType());
          dt.colorTrigger = [colorTrigger(sensor="<colorSensor>", color="<color>")];
          c.define("<idNew>", triggerId(), idNew, dt);
     }
     else if(/(DistanceTrigger)`INDISTANCE <DistanceSensor distanceSensor> <NATURAL distance>` := roverTrigger) {
          dt = defType(distanceTriggerType());
          dt.distanceTrigger = [distanceTrigger(sensor="<distanceSensor>", distance=toInt("<distance>"))];
          c.define("<idNew>", triggerId(), idNew, dt);
     }
     else if(/(TouchTrigger)`TOUCH <TouchSensor touchSensor>`:= roverTrigger) {
          dt = defType(touchTriggerType());
          dt.touchTrigger = [touchTrigger(sensor="<touchSensor>")];
          c.define("<idNew>", triggerId(), idNew, dt);
     }
     else {
          c.report(error(current, "unknown trigger type"));
     }
     collect(roverTrigger, c);
}

//CONCATENATION
void collect(current: (Trigger) `<ID idNew> <TriggerAssignment triggerAssignment> <IDList idTriggerList>`,  Collector c) {
     triggerList = collectIdList(c, idTriggerList, triggerId());

     dt = defType(idListType());
     dt.idList = [idList(idList=triggerList)];
     c.define("<idNew>", triggerId(), idNew, dt);
     collect(idTriggerList, c);

     c.calculate("trigger idList assignment", current, [idNew, idTriggerList],
          AType (Solver s) { 
               checkIdList(current, s, idTriggerList, 
               [colorTriggerType(), distanceTriggerType(), touchTriggerType(), idListType()], ["<idNew>"]);
               return idListType();
     });
}


// action

void collect(current: (RoverAction) `<RoverAction roverAction>`, Collector c) {
     if(/(MoveAction) `<MoveAction moveAction>` := roverAction) {
          c.fact(moveAction, moveActionType());
     }
     else if(/(TurnAction) `<TurnAction turnAction>` := roverAction) {
          c.fact(turnAction, turnActionType());
     }
     else if(/(SpeakAction) `<SpeakAction speakAction>` := roverAction) {
          c.fact(speakAction, speakActionType());
     }
     else if(/(LedAction) `<LedAction ledAction>` := roverAction) {
          c.fact(ledAction, ledActionType());
     }
}

//DEFINITION
void collect(current: (Action)`<ID idNew> <ActionAssignment actionAssignment> <RoverAction roverAction>`,  Collector c) {
     if(/(MoveAction) `<MoveAction moveAction>` := roverAction) {
          dt = createMoveAction(moveAction);
          c.define("<idNew>", actionId(), idNew, dt);
     }
     else if(/(TurnAction) `TURN <ANGLE angle>` := roverAction) {
          dt = defType(turnActionType());
          dt.turnAction = [turnAction(angle=toInt("<angle>"))];
          c.define("<idNew>", actionId(), idNew, dt);
     }
     else if(/(SpeakAction) `<SpeakAction speakAction>` := roverAction) {
          dt = createSpeakAction(speakAction);
          c.define("<idNew>", actionId(), idNew, dt);
     }
     else if(/(LedAction) `LED <ColorWritable color>` := roverAction) {
          dt = defType(ledActionType());
          dt.ledAction = [ledAction(color="<color>")];
          c.define("<idNew>", actionId(), idNew, dt);
     }
     collect(roverAction, c);
}

DefInfo createMoveAction(action) {
     dt = defType(moveActionType());
     if (/(MoveAction) `STOP` := action) {
          dt.moveAction = [moveAction(direction="stop", distance=0)];
     }
     else if (/(MoveAction) `FORWARD <NATURAL distance>` := action) {
          dt.moveAction = [moveAction(direction="forward", distance=toInt("<distance>"))];
     }
     else if (/(MoveAction) `BACKWARD <NATURAL distance>` := action) {
          dt.moveAction = [moveAction(direction="backward", distance=toInt("<distance>"))];
     }
     return dt;
}

DefInfo createSpeakAction(action) {
     dt = defType(speakActionType());
     if (/(SpeakAction) `SPEAK <STR text>` := action) {
          dt.speakAction = [speakAction(text="<text>")];
     }
     else if (/(SpeakAction) `BEEP` := action) {
          dt.speakAction = [speakAction(text="&.&.&.")]; // random unique text
     }
     return dt;
}



//CONCATENATION
void collect(current: (Action) `<ID idNew> <ActionAssignment actionAssignment> <IDList idActionList>`,  Collector c) {
     actionList = collectIdList(c, idActionList, actionId());

     dt = defType(idListType());
     dt.idList = [idList(idList=actionList)];
     c.define("<idNew>", actionId(), idNew, dt);
     collect(idActionList, c);

     c.calculate("trigger idList assignment", current, [idNew, idActionList],
          AType (Solver s) { 
               checkIdList(current, s, idActionList, 
               [moveActionType(), turnActionType(), speakActionType(), ledActionType(), idListType()], ["<idNew>"]);
               return idListType();
     });
}



// behavior

//definitions
// 1 trigger, 1 action
void collect(current: (Behavior)`Behavior: <ID idNew> WHEN <ID idTrigger> DO <ID idAction>`,  Collector c) {
     c.use(idTrigger, {triggerId()});
     c.use(idAction, {actionId()});
     dt = defType(behaviorType());
     dt.behavior = [behavior(triggerList=[idTrigger.src], actionList=[idAction.src], triggerListMod="ALL")];
     c.define("<idNew>", behaviorId(), idNew, dt);
}

// 1 trigger, n action
void collect(current: (Behavior)`Behavior: <ID idNew> WHEN <ID idTrigger> DO <IDList idActions>`,  Collector c) {
     c.use(idTrigger, {triggerId()});

     actionList = collectIdList(c, idActions, actionId());
     collect(idActions, c);
     c.calculate("action idList check", current, [idActions],
          AType (Solver s) { 
               checkIdList(current, s, idActions, 
               [moveActionType(), turnActionType(), touchTriggerType(), speakActionType(), ledActionType(), idListType()], []);
               return idListType();
     });

     dt = defType(behaviorType());
     dt.behavior = [behavior(triggerList=[idTrigger.src], actionList=actionList, triggerListMod="ALL")];
     c.define("<idNew>", behaviorId(), idNew, dt);
}

// n trigger, 1 action
void collect(current: (Behavior)`Behavior: <ID idNew> WHEN <ListMod listMod> <IDList idTriggers> DO <ID idAction>`,  Collector c) {
     c.use(idAction, {actionId()});

     triggerList = collectIdList(c, idTriggers, triggerId());
     collect(idTriggers, c);
     c.calculate("trigger idList check", current, [idTriggers],
          AType (Solver s) { 
               checkIdList(current, s, idTriggers, 
               [colorTriggerType(), distanceTriggerType(), touchTriggerType(), idListType()], []);
               return idListType();
     });

     dt = defType(behaviorType());
     dt.behavior = [behavior(triggerList=triggerList, actionList=[idAction.src], triggerListMod="<listMod>")];
     c.define("<idNew>", behaviorId(), idNew, dt);
}

// n trigger, n action
void collect(current: (Behavior)`Behavior: <ID idNew> WHEN <ListMod listMod> <IDList idTriggers> DO <IDList idActions>`,  Collector c) {
     actionList = collectIdList(c, idActions, actionId());
     collect(idActions, c);
     c.calculate("action idList check", current, [idActions],
          AType (Solver s) { 
               checkIdList(current, s, idActions, 
               [moveActionType(), turnActionType(), touchTriggerType(), speakActionType(), ledActionType(), idListType()], []);
               return idListType();
     });

     triggerList = collectIdList(c, idTriggers, triggerId());
     collect(idTriggers, c);
     c.calculate("trigger idList check", current, [idTriggers],
          AType (Solver s) { 
               checkIdList(current, s, idTriggers, 
               [colorTriggerType(), distanceTriggerType(), touchTriggerType(), idListType()], []);
               return idListType();
     });

     dt = defType(behaviorType());
     dt.behavior = [behavior(triggerList=triggerList, actionList=actionList, triggerListMod="<listMod>")];
     c.define("<idNew>", behaviorId(), idNew, dt);
}


// mission

//definitions
// 1 trigger, 1 action
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <ID idTask> WHILE <ID idBhv>`,  Collector c) {
     c.use(idTask, {triggerId()});
     c.use(idBhv, {behaviorId()});
     dt = defType(missionType());
     dt.mission = [mission(taskList=[idTask.src], behaviorList=[idBhv.src], taskListMod="ALL")];
     c.define("<idNew>", missionId(), idNew, dt);
}

// 1 trigger, n action
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <ID idTask> WHILE <IDList idBhvs>`,  Collector c) {
     c.use(idTask, {triggerId()});

     behaviorList = collectIdList(c, idBhvs, behaviorId());
     collect(idBhvs, c);

     dt = defType(missionType());
     dt.mission = [mission(taskList=[idTask.src], behaviorList=behaviorList,  taskListMod="ALL")];
     c.define("<idNew>", missionId(), idNew, dt);
}

// n trigger, 1 action
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <ListMod listMod> <IDList idTasks> WHILE <ID idBhv>`,  Collector c) {
     c.use(idBhv, {behaviorId()});

     taskList = collectIdList(c, idTasks, triggerId());
     collect(idTasks, c);

     dt = defType(missionType());
     dt.mission = [mission(taskList=taskList, behaviorList=[idBhv.src], taskListMod="<listMod>")];
     c.define("<idNew>", missionId(), idNew, dt);
}

// n trigger, n action
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <ListMod listMod> <IDList idTasks> WHILE <IDList idBhvs>`,  Collector c) {
     behaviorList = collectIdList(c, idBhvs, behaviorId());
     collect(idBhvs, c);

     taskList = collectIdList(c, idTasks, triggerId());
     collect(idTasks, c);

     dt = defType(missionType());
     dt.mission = [mission(taskList=taskList, behaviorList=behaviorList, taskListMod="<listMod>")];
     c.define("<idNew>", missionId(), idNew, dt);
}



// Roverconfig

void collect(current: (RoverConfig)`Rover: PERFORM <IDList missions> MAC: <STR macAddress>`, Collector c) {
     collect(missions, c);
     collectIdList(c, missions, missionId());
}