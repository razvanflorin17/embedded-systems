module Syntax

layout Layout = WhitespaceAndComment* !>> [\ \t\n\r#];
lexical WhitespaceAndComment = [\ \t\n\r] | @category="Comment" "#" ![\n]* $;

// With references and TypePal

start syntax Planning 
    = planning: (Trigger | Action | Behavior | Mission)+ 
    RoverConfig? roverConfig
;

syntax RoverConfig  //W.I.P.
    = new: "Rover:" IDList missions "MAC:" STR macAddress 
;

syntax Mission = "Mission:" ID id "EXECUTE" (Task | TaskList) tasks "WHILE" (ID | IDList) behaviors MissionFeedback? missionFeedback;

syntax Behavior
    = newSingleTrigger: "Behavior:" ID id "WHEN" ID trigger "DO" (ID | IDList) action
    | newMultiTrigger: "Behavior:" ID id "WHEN" ListMod? listMod IDList triggerList "DO" (ID | IDList) action
;


syntax MissionFeedback = "FEEDBACKS:" "{""START" IDList? startFeedback "," "END" IDList? endFeedback "," "TIMEOUT" IDList? timeoutFeedback "}";


syntax Task 
    = triggerListTask: '{' ListMod? listMod IDList triggerIdList Time? timeout '}'
    | triggerId: '{' ID idTrigger Time? timeout'}'
    | actionListTask: IDList actionIdList Time? timeout
    | actionTask: ID idAction Time? timeout
;


syntax Action
    = new: ID idNew ActionAssignment assignment RoverAction roverAction
    | copyList: ID idNew ActionAssignment assignment IDList idList
;

syntax Trigger
    = new: ID idNew TriggerAssignment assignment RoverTrigger roverTrigger
    | copyList: ID idNew TriggerAssignment assignment IDList idList 
;

syntax RoverAction
    = moveAction: MoveAction moveAction
    | turnAction: TurnAction turnAction 
    | speakAction: SpeakAction speakAction
    | ledAction: LedAction ledAction
    | measureAction: MeasureAction measureAction
;

syntax MoveAction
    = forward: "FORWARD" Distance distance Speed? speed
    | backward: "BACKWARD" Distance distance Speed? speed
    | stop: "STOP"
;


syntax TurnAction 
    = turnLeft: "LEFT" ANGLE angle Speed? speed
    | turnRight: "RIGHT" ANGLE angle Speed? speed
    | turnRandom: "RANDOM" ANGLE angle Speed? speed
;


syntax SpeakAction
    = speak: "SPEAK" STR text
    | beep: "BEEP"
;

syntax LedAction = "LED" ColorWritable color;
syntax ColorWritable
    = "red" | "green" | "blue" | "black" | "yellow" | "amber" | "orange";

syntax MeasureAction = "MEASURE" Time? time;

syntax RoverTrigger
    = colorRoverTrigger: ColorTrigger colorTrigger
    | distanceRoverTrigger: DistanceTrigger distanceTrigger
    | touchRoverTrigger: TouchTrigger touchTrigger
;

syntax ColorTrigger = "COLOR" ColorSensor colorSensor ColorReadable color;
syntax ColorSensor = "left" | "right" | "mid";
syntax ColorReadable = "black" | "blue" | "green" | "yellow" | "red" | "white" | "brown";

syntax DistanceTrigger = "INDISTANCE" DistanceSensor distanceSensor Distance distanceThreshold;
syntax DistanceSensor = "front" | "back";

syntax TouchTrigger = "TOUCH" TouchSensor touchSensor;
syntax TouchSensor = "left" | "right" | "back" | "any";

syntax ActionAssignment = actionAssignment: ':=';
syntax TriggerAssignment = triggerAssignment: '==';

syntax IDList
    = explicit: '[' {IDListComponent ','}+ ']'
    | implicit: IDListComponent idComponent '+' {IDListComponent '+'}+
    | pow: ID '^' NATURAL power
;

syntax IDListComponent
    = id: ID id
    | powId: ID '^' NATURAL power
;


syntax ListMod
    = "ANY"
    | "ALL"
    | "ALLORD"
    | "SIM" // stand for "SIMULTANEOUS"
;

syntax TaskList 
    = explicit: '[' {Task ','}+ ']'
    | implicit: Task task '+' {Task '+'}+
;

syntax DistanceUnit = "cm" | "m" | "mm" | "dm"; 
syntax Distance = NATURAL distance DistanceUnit? distanceUnit;
syntax Time = NATURAL time TimeUnit? timeUnit;
syntax TimeUnit = "s" | "min" | "h";
syntax Speed = PERCENTAGE speed;


lexical INT = ([\-0-9][0-9]* !>> [0-9]);
lexical NATURAL = ([0-9][0-9]* !>> [0-9]);
lexical ANGLE = (([0-9]?[0-9]) | ([0-2][0-9][0-9]) | ([3-3][0-5][0-9]) | ([3-3][6-6][0-0]))"°"?;
lexical PERCENTAGE = (([0-9]?[0-9]) | ([1-1][0-0][0-0]))"%"?;
lexical ID = ([a-z/.\-][a-zA-Z0-9_/.]* !>> [a-zA-Z0-9_/.]) \ Reserved; 
lexical STR = "\"" ![\"\n]* "\"";

keyword Reserved = "Mission:" | "Behavior:" | "WHEN" | "WHILE" | "DO" |"green" | "red" | "blue" | "black" | "yellow" | "amber" | "orange" | "°" | "%" | "m" | "dm" | "cm" | "mm"
        | "FORWARD" | "BACKWARD" | "TURN" | "SPEAK" | "LED"| "BEEP" | "MEASURE" | "ANY" | "ALL" | "ALLORD" | "FEEDBACKS:" | "START" | "END" | "TIMEOUT" | ":" | "left" | "right" | "LEFT" | "RIGHT" | "mid" | "back" | "front" | "EXECUTE" | "PERFORM" | "MAC:";
