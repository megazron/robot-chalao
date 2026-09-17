// Robot Chalao -- native C++ core entry point.
//   chalao run FILE [--simulate]   run a .rc program (simulation backend)
//   chalao repl                    interactive prompt
//   chalao --version
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include "value.hpp"
#include "ast.hpp"
#include "lexer.hpp"
#include "parser.hpp"
#include "interp.hpp"

static const char* VERSION = "0.1.0 (native)";

static int runFile(const std::string& path) {
    std::ifstream f(path);
    if (!f) { std::cerr << "Bhai, file nahi khuli: " << path << " (file not found)\n"; return 2; }
    std::stringstream ss; ss << f.rdbuf();
    try {
        NodePtr prog = parseSource(ss.str());
        Interpreter interp(true);
        interp.run(prog);
    } catch (RCError& e) {
        std::cerr << e.what_hinglish() << "\n";
        return 1;
    }
    return 0;
}

static int repl() {
    std::cout << "Robot Chalao " << VERSION << " -- REPL. 'bye' se niklo.\n";
    Interpreter interp(true);
    std::string buf, line;
    while (true) {
        std::cout << (buf.empty() ? "chalao> " : "   ...> ") << std::flush;
        if (!std::getline(std::cin, line)) break;
        if (buf.empty() && (line == "bye" || line == "exit")) break;
        buf += line + "\n";
        try {
            NodePtr prog = parseSource(buf);
            interp.run(prog);
            buf.clear();
        } catch (RCError& e) {
            if (e.hint_en.find("not closed") != std::string::npos) continue;  // need more lines
            std::cerr << e.what_hinglish() << "\n";
            buf.clear();
        }
    }
    return 0;
}

int main(int argc, char** argv) {
    std::string cmd = argc > 1 ? argv[1] : "";
    if (cmd == "--version" || cmd == "-v") { std::cout << "chalao " << VERSION << "\n"; return 0; }
    if (cmd == "repl") return repl();
    if (cmd == "run") {
        std::string file;
        for (int i = 2; i < argc; ++i) { std::string a = argv[i]; if (a == "--simulate" || a == "--sim") continue; file = a; }
        if (file.empty()) { std::cerr << "Bhai, kaunsi file chalau? use: chalao run FILE\n"; return 2; }
        return runFile(file);
    }
    // `chalao file.rc` shorthand
    if (!cmd.empty() && cmd[0] != '-') return runFile(cmd);
    std::cout << "Robot Chalao " << VERSION << "\n"
              << "use: chalao run FILE [--simulate]\n"
              << "     chalao repl\n"
              << "     chalao --version\n";
    return 0;
}
