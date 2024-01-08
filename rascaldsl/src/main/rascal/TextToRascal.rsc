module TextToRascal

import IO;
import List;
import String;

public int main(list[str] args=[]) {
    master_input = |project://rascaldsl/instance/static_code/master_input.py|;
    master_output = |project://rascaldsl/instance/static_code/master_output.py|;
    
    slave_input = |project://rascaldsl/instance/static_code/slave_input.py|;
    slave_output = |project://rascaldsl/instance/static_code/slave_output.py|;
    
    convertFile(master_input, master_output);
    convertFile(slave_input, slave_output);
    return 0;
}


void convertFile(loc inputFile, loc outputFile) {
    assert exists(inputFile);
    input = readFile(inputFile);
    output = convert(input);
    writeFile(outputFile, output);
}

str convert(str input) {
    firstLine = true;
    output = "";
    lines = split("\r\n", input);
    for (l <- lines) {
        l = replaceAll(l, "\"", "\\\"");
        l = replaceAll(l, "\'", "\\\'");
        l = replaceAll(l, "\<", "\\\<");
        l = replaceAll(l, "\>", "\\\>");
        if (firstLine) {
            output += "    rVal += \"<l>\n";
        } else {
            output += "            \'<l>\n";
        }
        firstLine = false;
    }
    output += "            \'\";";
    return output;
}
