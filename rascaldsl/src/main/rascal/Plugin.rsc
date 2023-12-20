module Plugin

import IO;
import ParseTree;
import util::Reflective;
import util::IDEServices;
import util::LanguageServer;
import Relation;

import Syntax;
import Checker;
import Generator;

PathConfig pcfg = getProjectPathConfig(|project://rascaldsl|, mode=interpreter());
Language tdslLang = language(pcfg, "TDSL", "tdsl", "Plugin", "contribs");

data Command = gen(Planning p);

Summary tdslSummarizer(loc l, start[Planning] input) {
    tm = modulesTModelFromTree(input);
    defs = getUseDef(tm);
    return summary(l, messages = {<m.at, m> | m <- getMessages(tm), !(m is info)}, definitions = defs);
}
set[LanguageService] contribs() = {
    parser(start[Planning] (str program, loc src) {
        return parse(#start[Planning], program, src);
    }),
    lenses(rel[loc src, Command lens] (start[Planning] p) {
        return {
            <p.src, gen(p.top, title="Generate python file (remember to save)")>
        };
    }),
    summarizer(tdslSummarizer),
    executor(exec)
};

value exec(gen(Planning p)) {
    rVal = generator(p);
    outputFile = |project://rascaldsl/instance/output/output.py|; 
    writeFile(outputFile, rVal);
    edit(outputFile);
    return ("result": true);
}


void main() {
    registerLanguage(tdslLang);
}
