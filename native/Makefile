# Robot Chalao -- native C++ core
CXX ?= g++
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Werror -Iinclude
BIN := chalao

$(BIN): src/main.cpp $(wildcard include/*.hpp)
	$(CXX) $(CXXFLAGS) src/main.cpp -o $(BIN)

.PHONY: test san clean
test: $(BIN)
	bash tests/run_tests.sh

# memory-safety build: run `make san && ./chalao ...` or `make san test`
san: CXXFLAGS := -std=c++17 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -Iinclude
san: clean $(BIN)

clean:
	rm -f $(BIN)
