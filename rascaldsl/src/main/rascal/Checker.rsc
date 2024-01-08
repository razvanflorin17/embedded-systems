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
     | measureActionType()
     | behaviorType()
     | missionType()
;

// ADT definitions

data ColorTrigger = colorTrigger(str sensor = "", str color = "");
data DistanceTrigger = distanceTrigger(str sensor = "", int distance = 0);
data TouchTrigger = touchTrigger(str sensor = "");

data IDList = idList(list[loc] idList = []);

data MoveAction = moveAction(str direction = "", int distance = 0, int speed = 15);
data TurnAction = turnAction(str direction = "", int angle = 0, int speed = 10);
data SpeakAction = speakAction(str text = "");
data LedAction = ledAction(str color = "");
data MeasureAction = measureAction(int time=1, str target = "");

data Behavior = behavior(list[loc] triggerList = [], list[loc] actionList = [], str triggerListMod="ALL");
data Task = task(list[loc] activityList = [], str activityType="TRIGGER", str activityListMod="ALL", int timeout=60);
data Mission = mission(list[Task] taskList = [], list[loc] behaviorList = [], tuple[list[loc], list[loc], list[loc]] feedbacks = <[], [], []>);

// ADT constructors

data DefInfo(list[ColorTrigger] colorTrigger = []);
data DefInfo(list[DistanceTrigger] distanceTrigger = []);
data DefInfo(list[TouchTrigger] touchTrigger = []);

data DefInfo(list[IDList] idList = []);

data DefInfo(list[MoveAction] moveAction = []);
data DefInfo(list[TurnAction] turnAction = []);
data DefInfo(list[SpeakAction] speakAction = []);
data DefInfo(list[LedAction] ledAction = []);
data DefInfo(list[MeasureAction] measureAction = []);

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

void checkIdList(Solver s, idCheckList, list[AType] validTypes, list[str] excludedIds) {
     for (<id> <- [<id> |/(ID) `<ID id>` := idCheckList]) {
          s.requireFalse(("<id>" in excludedIds), error(id, "%v is excluded", "<id>"));
          s.requireTrue((s.getType(id) in validTypes), error(id,  "type should be one of %v, instead of %t", validTypes, id));
     }
}

list[loc] collectIdList(Collector c, idCollectList, role) {
     result = [];
     if(/(IDList) `<ID id> ^ <NATURAL power>` := idCollectList) {
          pow = toInt("<power>");
          if (pow == 0) c.report(error(power, "power should be greater than 0"));
          c.use(id, {role});
          for (i <- [0..pow]) result += id.src;
     }
     else for (<idC> <- [<idComponent> |/(IDListComponent) `<IDListComponent idComponent>` := idCollectList]) {
          if(/(IDListComponent) `<ID id>` := idC) {
               c.use(id, {role});
               result += id.src;
          }
          else if(/(IDListComponent) `<ID id> ^ <NATURAL power>` := idC) {
               c.use(id, {role});
               pow = toInt("<power>");
               if (pow == 0) c.report(error(power, "power should be greater than 0"));
               for (i <- [0..pow]) result += id.src;
          }

     }
     return result;
}

list[loc] collectFeedback(Collector c, feedback) {
     feedbackList = collectIdList(c, feedback, actionId());
     collect(feedback, c);
     c.calculate("feedback idList check", feedback, [],
     AType (Solver s) { 
          checkIdList(s, feedback, [speakActionType(), ledActionType()], []);
          return idListType();
     });
     return feedbackList;
}

tuple[list[loc], list[loc], list[loc]] collectFeedbacks(Collector c, mission) {
     list[loc] feedbackStartList = [];
     list[loc] feedbackEndList = [];
     list[loc] feedbackTimeoutList = [];
     if (/(MissionFeedback) `<MissionFeedback feedbacks>` := mission) {
          if (/(MissionFeedback)`FEEDBACKS: {START <IDList startFeedback>, END <IDList? _>, TIMEOUT <IDList? _>}` := feedbacks) 
               feedbackStartList += collectFeedback(c, startFeedback);

          if (/(MissionFeedback)`FEEDBACKS: {START <IDList? _>, END <IDList endFeedback>, TIMEOUT <IDList? _>}` := feedbacks) 
               feedbackEndList = collectFeedback(c, endFeedback);
          
          if (/(MissionFeedback)`FEEDBACKS: {START <IDList? _>, END <IDList? _>, TIMEOUT <IDList timeoutFeedback>}` := feedbacks)
               feedbackTimeoutList = collectFeedback(c, timeoutFeedback);
     }
     return <feedbackStartList, feedbackEndList, feedbackTimeoutList>;
}

int computeDistance(distance) {
     if(/(Distance) `<NATURAL distance>` := distance) {
          return toInt("<distance>");
     }
     else if(/(Distance) `<NATURAL distance> <DistanceUnit unit>` := distance) {
          int distance_value = toInt("<distance>");
          if(/(DistanceUnit) `cm` := unit) return distance_value;
          else if(/(DistanceUnit) `m` := unit) return distance_value * 100;
          else if(/(DistanceUnit) `mm` := unit) return distance_value / 10;
          else if(/(DistanceUnit) `dm` := unit) return distance_value * 10;
     }
     return 0;
}

int computeTime(time_input) {
     if(/(Time) `<NATURAL time>` := time_input) {
          return toInt("<time>");
     }
     else if(/(Time) `<NATURAL time> <TimeUnit unit>` := time_input) {
          int time_value = toInt("<time>");
          if(/(TimeUnit) `s` := unit) return time_value;
          else if(/(TimeUnit) `min` := unit) return time_value * 60;
          else if(/(TimeUnit) `h` := unit) return time_value * 3600;
     }
     return 0;
}

// typepal collectors

void collect(current: (IDList)`<IDList idlist>`, Collector c) {
     c.fact(idlist, idListType());
}

//  Trigger

void collect(current: (RoverTrigger) `COLOR <ColorSensor colorSensor> <ColorReadable color>`, Collector c) {
     c.fact(current, colorTriggerType());
}

void collect(current: (RoverTrigger) `INDISTANCE <DistanceSensor distanceSensor> <Distance distance>`, Collector c) {
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
     else if(/(DistanceTrigger)`INDISTANCE <DistanceSensor distanceSensor> <Distance distance>` := roverTrigger) {
          dt = defType(distanceTriggerType());
          dt.distanceTrigger = [distanceTrigger(sensor="<distanceSensor>", distance=computeDistance(distance))];
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
               checkIdList(s, idTriggerList, 
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
     else if(/(MeasureAction) `<MeasureAction measureAction>` := roverAction) {
          c.fact(measureAction, measureActionType());
     }
}

//DEFINITION
void collect(current:(Action)`<ID idNew> <ActionAssignment actionAssignment> <RoverAction roverAction>`,  Collector c) {
     if(/(MoveAction) `<MoveAction moveAction>` := roverAction) {
          dt = createMoveAction(moveAction, c);
          c.define("<idNew>", actionId(), idNew, dt);
     }
     else if(/(TurnAction) `<TurnAction turnAction>` := roverAction) {
          dt = createTurnAction(turnAction, c);
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
     else if(/(MeasureAction) `<MeasureAction measureAction>` := roverAction) {
          dt = createMeasureAction(measureAction, c);
          c.define("<idNew>", actionId(), idNew, dt);
     }

     collect(roverAction, c);
}

DefInfo createMoveAction(action, Collector c) {
     dt = defType(moveActionType());
     speed_value = 15; // default speed for moving

     if(/(Speed) `<PERCENTAGE speed>` := action) {
          speed_value = toInt(replaceLast("<speed>", "%", ""));
          if (speed_value > 30) c.report(warning(speed, "speed higher than 30%% could be dangerous"));
     }

     if (/(MoveAction) `STOP` := action) {
          dt.moveAction = [moveAction(direction="stop", distance=0)];
     }
     else if (/(MoveAction) `FORWARD <Distance distance> <Speed? _>` := action) {
          dt.moveAction = [moveAction(direction="forward", distance=computeDistance(distance), speed=speed_value)];
     }
     else if (/(MoveAction) `BACKWARD <Distance distance> <Speed? _>` := action) {
          dt.moveAction = [moveAction(direction="backward", distance=computeDistance(distance), speed=speed_value)];
     }
     return dt;
}

DefInfo createTurnAction(action, Collector c) {
     dt = defType(turnActionType());
     speed_value = 10; // default speed for turning

     if(/(Speed) `<PERCENTAGE speed>` := action) {
          speed_value = toInt(replaceLast("<speed>", "%", ""));
          if (speed_value > 30) c.report(warning(speed, "speed higher than 30%% could be dangerous"));

     }
 
     if (/(TurnAction) `LEFT <ANGLE angle> <Speed? _>` := action) {
          dt.turnAction = [turnAction(direction="left", angle=toInt(replaceLast("<angle>", "°", "")), speed=speed_value)];
     }
     else if (/(TurnAction) `RIGHT <ANGLE angle> <Speed? _>` := action) {
          dt.turnAction = [turnAction(direction="right", angle=toInt(replaceLast("<angle>", "°", "")), speed=speed_value)];
     }
     else if (/(TurnAction) `RANDOM <ANGLE angle> <Speed? _>` := action) {
          dt.turnAction = [turnAction(direction="none", angle=toInt(replaceLast("<angle>", "°", "")), speed=speed_value)];
     }
     
     return dt;
}


DefInfo createMeasureAction(action, Collector c) {
     dt = defType(measureActionType());
     time_value = 1;
     if (/(Time) `<Time time>` := action) time_value = computeTime(time);
     if (/(MeasureAction)`MEASURE LAKE <ColorReadable color> <Time? _>` := action) {
          if ("<color>" == "white" || "<color>" == "black") c.report(error(color, "<color> is not a valid color for lake"));
          dt.measureAction = [measureAction(time=time_value, target="<color>")];
     }
     else if (/(MeasureAction)`MEASURE OBJECT <Time? _>` := action) {
          dt.measureAction = [measureAction(time=time_value, target="object")];
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
               checkIdList(s, idActionList, 
               [moveActionType(), turnActionType(), speakActionType(), ledActionType(), measureActionType(), idListType()], ["<idNew>"]);
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
               checkIdList(s, idActions, 
               [moveActionType(), turnActionType(), touchTriggerType(), speakActionType(), ledActionType(), measureActionType(), idListType()], []);
               return idListType();
     });

     dt = defType(behaviorType());
     dt.behavior = [behavior(triggerList=[idTrigger.src], actionList=actionList, triggerListMod="ALL")];
     c.define("<idNew>", behaviorId(), idNew, dt);
}

// n trigger, 1 action
void collect(current: (Behavior)`Behavior: <ID idNew> WHEN <ListMod? listMod> <IDList idTriggers> DO <ID idAction>`,  Collector c) {
     c.use(idAction, {actionId()});

     triggerList = collectIdList(c, idTriggers, triggerId());
     collect(idTriggers, c);
     c.calculate("trigger idList check", current, [idTriggers],
          AType (Solver s) { 
               checkIdList(s, idTriggers, 
               [colorTriggerType(), distanceTriggerType(), touchTriggerType(), idListType()], []);
               return idListType();
     });

     listMod_value = "ALL";
     if(current has listMod)  {
          listMod_value = "<listMod>";
          if (listMod_value == "SIM") listMod_value = "ALL";
     }

     dt = defType(behaviorType());
     dt.behavior = [behavior(triggerList=triggerList, actionList=[idAction.src], triggerListMod=listMod_value)];
     c.define("<idNew>", behaviorId(), idNew, dt);
}

// n trigger, n action
void collect(current: (Behavior)`Behavior: <ID idNew> WHEN <ListMod? listMod> <IDList idTriggers> DO <IDList idActions>`,  Collector c) {
     actionList = collectIdList(c, idActions, actionId());
     collect(idActions, c);
     c.calculate("action idList check", current, [idActions],
          AType (Solver s) { 
               checkIdList(s, idActions, 
               [moveActionType(), turnActionType(), touchTriggerType(), speakActionType(), ledActionType(), measureActionType(), idListType()], []);
               return idListType();
     });

     triggerList = collectIdList(c, idTriggers, triggerId());
     collect(idTriggers, c);
     c.calculate("trigger idList check", current, [idTriggers],
          AType (Solver s) { 
               checkIdList(s, idTriggers, 
               [colorTriggerType(), distanceTriggerType(), touchTriggerType(), idListType()], []);
               return idListType();
     });

     listMod_value = "ALL";
     if(current has listMod)  {
          listMod_value = "<listMod>";
          if (listMod_value == "SIM") listMod_value = "ALL";
     }
     
     dt = defType(behaviorType());
     dt.behavior = [behavior(triggerList=triggerList, actionList=actionList, triggerListMod=listMod_value)];
     c.define("<idNew>", behaviorId(), idNew, dt);
}


// task
Task collectTask(Collector c, task_in) {
     int timeout_value = 60;
     if(/(Time) `<Time timeout>` := task_in) {
          timeout_value = computeTime(timeout);
          if (timeout_value <= 0) c.report(error(timeout, "timeout should be greater than 0"));
          else if (timeout_value < 30) c.report(warning(timeout, "timeout less than 30s may be too short"));
     }

     if(/(Task) `<ID idAction> <Time? _>` := task_in) {
          c.use(idAction, {actionId()});
          return task(activityList=[idAction.src], activityListMod="ALL", activityType="ACTION", timeout=timeout_value);
     } 
     if (/(Task) `{<ID idTrigger> <Time? _>}` := task_in) {
          c.use(idTrigger, {triggerId()});
          return task(activityList=[idTrigger.src], activityListMod="ALL", activityType="TRIGGER", timeout=timeout_value);
     }
     if (/(Task) `<IDList actionIdList> <Time? _>` := task_in) {
          actionList = collectIdList(c, actionIdList, actionId());
          collect(actionIdList, c);
          return task(activityList=actionList, activityListMod="ALL", activityType="ACTION", timeout=timeout_value);
     }
     if (/(Task) `{<IDList triggerIdList> <Time? _>}` := task_in) {
          triggerList = collectIdList(c, triggerIdList, triggerId());
          collect(triggerIdList, c);
          return task(activityList=triggerList, activityListMod="ALL", activityType="TRIGGER", timeout=timeout_value);
     }
     if (/(Task) `{<ListMod listMod> <IDList triggerIdList> <Time? _>}` := task_in) {
          triggerList = collectIdList(c, triggerIdList, triggerId());
          collect(triggerIdList, c);
          return task(activityList=triggerList, activityListMod="<listMod>", activityType="TRIGGER", timeout=timeout_value);
     }

     return task(activityList=[], activityListMod="ALL", activityType="ACTION", timeout=timeout_value);
}

// mission

//definitions
// 1 task, 1 bhv
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <Task task> WHILE <ID idBhv> <MissionFeedback? missionFeedback>`,  Collector c) {
     task_res = collectTask(c, task);
     c.use(idBhv, {behaviorId()});

     dt = defType(missionType());
     dt.mission = [mission(taskList=[task_res], behaviorList=[idBhv.src], feedbacks=collectFeedbacks(c, missionFeedback))];
     c.define("<idNew>", missionId(), idNew, dt);
}

// 1 task, n bhv
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <Task task> WHILE <IDList idBhvs> <MissionFeedback? missionFeedback>`,  Collector c) {
     task_res = collectTask(c, task);

     behaviorList = collectIdList(c, idBhvs, behaviorId());
     collect(idBhvs, c);

     dt = defType(missionType());
     dt.mission = [mission(taskList=[task_res], behaviorList=behaviorList, feedbacks=collectFeedbacks(c, missionFeedback))];
     c.define("<idNew>", missionId(), idNew, dt);
}

// n task, 1 bhv
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <TaskList tasks> WHILE <ID idBhv> <MissionFeedback? missionFeedback>`,  Collector c) {
     c.use(idBhv, {behaviorId()});

     taskList_res = [];
     for (task_in <- [task_in |/(Task) `<Task task_in>` := tasks]) {
          taskList_res += collectTask(c, task_in);
     } 

     dt = defType(missionType());
     dt.mission = [mission(taskList=taskList_res, behaviorList=[idBhv.src], feedbacks=collectFeedbacks(c, missionFeedback))];
     c.define("<idNew>", missionId(), idNew, dt);
}

// n task, n bhv
void collect(current: (Mission)`Mission: <ID idNew> EXECUTE <TaskList tasks> WHILE <IDList idBhvs> <MissionFeedback? missionFeedback>`,  Collector c) {
     behaviorList = collectIdList(c, idBhvs, behaviorId());
     collect(idBhvs, c);

     taskList_res = [];
     for (task_in <- [task_in |/(Task) `<Task task_in>` := tasks]) {
          taskList_res += collectTask(c, task_in);
     }

     dt = defType(missionType());
     dt.mission = [mission(taskList=taskList_res, behaviorList=behaviorList, feedbacks=collectFeedbacks(c, missionFeedback))];
     c.define("<idNew>", missionId(), idNew, dt);
}



// Roverconfig

void collect(current: (RoverConfig)`Rover: <IDList missions> MAC: <STR macAddress>`, Collector c) {
     collect(missions, c);
     collectIdList(c, missions, missionId());
}