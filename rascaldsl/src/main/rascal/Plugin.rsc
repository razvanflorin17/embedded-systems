module Plugin

import IO;
import ParseTree;
import util::Reflective;
import util::IDEServices;
import util::LanguageServer;
import Relation;

import Syntax;
import Checker;
import Static_Generator;
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
    static_code = static_code_generator();
    rVal = generator(p, static_code[0], static_code[1], static_code[2]);

    masterOutputFile = |project://rascaldsl/instance/output/master.py|;
    slaveOutputFile = |project://rascaldsl/instance/output/slave.py|; 
    writeFile(masterOutputFile, rVal[0]);
    writeFile(slaveOutputFile, rVal[1]);
    edit(masterOutputFile);
    return ("result": true);
}

void main() {
    registerLanguage(tdslLang);
}
