// Robot Chalao -- native C++ core entry point.
//   chalao run FILE [--simulate]   run a .rc program (simulation backend)
//   chalao check FILE...           parse only, report grammar errors
//   chalao repl                    interactive prompt
//   chalao --version
#include <cstdio>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include "value.hpp"
#include "ast.hpp"
#include "lexer.hpp"
#include "parser.hpp"
#include "interp.hpp"

static const char* VERSION = "1.0.1 (native)";

static bool readFile(const std::string& path, std::string& out) {
    std::ifstream f(path);
    if (!f) { std::cerr << "Bhai, file '" << path << "' nahi mili (file not found)\n"; return false; }
    std::stringstream ss; ss << f.rdbuf(); out = ss.str();
    return true;
}

// Same layout as the Python CLI: message, then `--> file:line` and the line.
static void report(const RCError& e, const std::string& path, const std::string& src) {
    std::cerr << e.what_hinglish() << "\n";
    if (e.line <= 0) return;
    std::cerr << "  --> " << path << ":" << e.line << "\n";
    std::istringstream in(src); std::string l;
    for (int i = 1; std::getline(in, l); ++i) {
        if (i != e.line) continue;
        while (!l.empty() && (l.back() == ' ' || l.back() == '\t' || l.back() == '\r')) l.pop_back();
        if (l.find_first_not_of(" \t") != std::string::npos) {
            char num[16]; std::snprintf(num, sizeof num, "%4d", e.line);
            std::cerr << "  " << num << " | " << l << "\n";
        }
        break;
    }
}

static int runFile(const std::string& path) {
    std::string src;
    if (!readFile(path, src)) return 1;
    try {
        NodePtr prog = parseSource(src);
        Interpreter interp(true);
        auto slash = path.find_last_of('/');
        interp.baseDir = (slash == std::string::npos) ? std::string(".") : path.substr(0, slash);
        interp.run(prog);
    } catch (RCError& e) {
        report(e, path, src);
        return 1;
    }
    return 0;
}

static int checkFiles(int argc, char** argv, int from) {
    int bad = 0;
    for (int i = from; i < argc; ++i) {
        std::string path = argv[i], src;
        if (!readFile(path, src)) { ++bad; continue; }
        try { parseSource(src); std::cout << "theek  " << path << "\n"; }
        catch (RCError& e) { report(e, path, src); ++bad; }
    }
    if (from >= argc) { std::cerr << "Bhai, kaunsi file check karu? use: chalao check FILE...\n"; return 2; }
    return bad ? 1 : 0;
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

static void usage(std::ostream& os) {
    os << "Robot Chalao " << VERSION << "\n"
       << "use: chalao run FILE [--simulate]   program chalao (nakli backend)\n"
       << "     chalao check FILE...           grammar check, bina chalaye\n"
       << "     chalao repl                    interactive shell\n"
       << "     chalao --version\n";
}

int main(int argc, char** argv) {
    std::string cmd = argc > 1 ? argv[1] : "";
    if (cmd == "--version" || cmd == "-v") { std::cout << "chalao " << VERSION << "\n"; return 0; }
    if (cmd == "--help" || cmd == "-h") { usage(std::cout); return 0; }
    if (cmd == "repl") return repl();
    if (cmd == "check") return checkFiles(argc, argv, 2);
    if (cmd == "run") {
        std::string file;
        for (int i = 2; i < argc; ++i) { std::string a = argv[i]; if (a == "--simulate" || a == "--sim") continue; file = a; }
        if (file.empty()) { std::cerr << "Bhai, kaunsi file chalau? use: chalao run FILE\n"; return 2; }
        return runFile(file);
    }
    // `chalao file.rc` shorthand
    if (!cmd.empty() && cmd[0] != '-') return runFile(cmd);
    usage(cmd.empty() ? std::cout : std::cerr);
    return cmd.empty() ? 0 : 2;
}
