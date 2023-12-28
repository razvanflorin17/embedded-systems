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

syntax Mission
    = newSingle: "Mission:" ID id "EXECUTE" ID task "WHILE" (ID | IDList) behaviors
    | newMulti: "Mission:" ID id "EXECUTE" ListMod? listMod IDList taskList "WHILE" (ID | IDList) behaviors
;

syntax Behavior
    = newSingleTrigger: "Behavior:" ID id "WHEN" ID trigger "DO" (ID | IDList) action
    | newMultiTrigger: "Behavior:" ID id "WHEN" ListMod? listMod IDList triggerList "DO" (ID | IDList) action
;


syntax Action
    = new: ID idNew ActionAssignment assignment RoverAction roverAction
    // | newList: ID idNew ActionAssignment assignment '[' {RoverAction ','}+ ']' //not implemented
    // | copy: ID idNew ActionAssignment assignment ID idOld   // not implemented
    | copyList: ID idNew ActionAssignment assignment IDList idList
;

syntax Trigger
    = new: ID idNew TriggerAssignment assignment RoverTrigger roverTrigger
    // | newList: ID idNew TriggerAssignment assignment '[' {RoverTrigger ','}+ ']' // not implemented
    // | copy: ID idNew TriggerAssignment assignment ID idOld    // not implemented
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

syntax Speed = PERCENTAGE speed;

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
    = explicit: '[' {ID ','}+ ']'
    | implicit: ID id '+' {ID '+'}+
;

syntax ListMod
    = "ANY"
    | "ALL"
    | "ALLORD"
;

syntax DistanceUnit = "cm" | "m" | "mm" | "dm"; 
syntax Distance = NATURAL distance DistanceUnit? distanceUnit;
syntax Time = NATURAL time TimeUnit? timeUnit;
syntax TimeUnit = "s" | "min" | "h";

lexical INT = ([\-0-9][0-9]* !>> [0-9]);
lexical NATURAL = ([0-9][0-9]* !>> [0-9]);
lexical ANGLE = (([0-9]?[0-9]) | ([0-2][0-9][0-9]) | ([3-3][0-5][0-9]) | ([3-3][6-6][0-0]))"°"?;
lexical PERCENTAGE = (([0-9]?[0-9]) | ([1-1][0-0][0-0]))"%"?;
lexical ID = ([a-z/.\-][a-zA-Z0-9_/.]* !>> [a-zA-Z0-9_/.]) \ Reserved; 
lexical STR = "\"" ![\"\n]* "\"";

keyword Reserved = "Mission:" | "Behavior:" | "WHEN" | "WHILE" | "DO" |"green" | "red" | "blue" | "black" | "yellow" | "amber" | "orange" | "°" | "%" | "m" | "dm" | "cm" | "mm"
        | "FORWARD" | "BACKWARD" | "TURN" | "SPEAK" | "LED"| "BEEP" | "MEASURE" | "ANY" | "ALL" | "ALLORD" | ":" | "left" | "right" | "LEFT" | "RIGHT" | "mid" | "back" | "front" | "EXECUTE" | "PERFORM" | "MAC:";
