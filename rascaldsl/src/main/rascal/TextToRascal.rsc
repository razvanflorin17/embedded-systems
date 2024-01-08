module TextToRascal

import IO;
import List;
import String;

public int main(list[str] args=[]) {
    common_input = |project://rascaldsl/instance/static_code/common_input.py|;
    common_output = |project://rascaldsl/instance/static_code/common_output.py|;

    master_input = |project://rascaldsl/instance/static_code/master_input.py|;
    master_output = |project://rascaldsl/instance/static_code/master_output.py|;
    
    slave_input = |project://rascaldsl/instance/static_code/slave_input.py|;
    slave_output = |project://rascaldsl/instance/static_code/slave_output.py|;
    
    convertFile("", common_input, common_output);
    convertFile("", master_input, master_output);
    convertFile("", slave_input, slave_output);
    return 0;
}


str convertFile(str static, loc inputFile, loc outputFile) {
    assert exists(inputFile);
    first_line = false;
    if (static == "") {
        first_line = true;
    }

    input = readFile(inputFile);
    output = static + "\n" + convert(input, first_line);
    writeFile(outputFile, output);

    return output;
}

str convert(str input, bool firstLine) {
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
