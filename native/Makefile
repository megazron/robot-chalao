# Robot Chalao -- native C++ core
CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Iinclude
BIN := chalao

$(BIN): src/main.cpp $(wildcard include/*.hpp)
	$(CXX) $(CXXFLAGS) src/main.cpp -o $(BIN)

.PHONY: test clean
test: $(BIN)
	bash tests/run_tests.sh

clean:
	rm -f $(BIN)
