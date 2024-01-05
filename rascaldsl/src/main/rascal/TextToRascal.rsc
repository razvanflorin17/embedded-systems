module TextToRascal

import IO;
import List;
import String;

public int main(list[str] args=[]) {
    inputFilePath = |project://rascaldsl/instance/static_code/input.py|;
    outputFilePath = |project://rascaldsl/instance/static_code/output.py|;
    outputFile = "";
    firstLine = true;

    assert exists(inputFilePath);
    input = readFile(inputFilePath);
    lines = split("\r\n", input);
    for (l <- lines) {
        l = replaceAll(l, "\"", "\\\"");
        l = replaceAll(l, "\'", "\\\'");
        l = replaceAll(l, "\<", "\\\<");
        l = replaceAll(l, "\>", "\\\>");
        if (firstLine) {
            outputFile += "    rVal += \"<l>\n";
        } else {
            outputFile += "            \'<l>\n";
        }
        firstLine = false;
    }
    outputFile += "            \'\";";

    println(outputFile);
    writeFile(outputFilePath, outputFile);
    return 0;
}
