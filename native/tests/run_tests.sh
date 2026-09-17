#!/usr/bin/env bash
# Build the native chalao binary, run feature tests against expected output,
# and run every example program expecting a clean exit. Exit nonzero on any failure.
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"
BIN="$HERE/chalao"
fail=0

echo "== building =="
make -s || { echo "BUILD FAILED"; exit 1; }

echo "== feature tests =="
for t in tests/t_*.rc; do
  exp="${t%.rc}.expected"
  got="$("$BIN" run "$t" 2>&1)"
  if [ "$got" == "$(cat "$exp")" ]; then
    echo "  PASS $(basename "$t")"
  else
    echo "  FAIL $(basename "$t")"; diff <(cat "$exp") <(printf '%s\n' "$got") | head -12; fail=1
  fi
done

echo "== example programs (expect exit 0) =="
for ex in ../examples/*.rc; do [ -e "$ex" ] || continue
  if "$BIN" run "$ex" >/dev/null 2>&1; then echo "  PASS $(basename "$ex")"; else echo "  FAIL $(basename "$ex") (nonzero exit)"; fail=1; fi
done

echo "== error handling (expect nonzero) =="
printf 'agar sach toh\n  dikhao "x"\n' > /tmp/rc_bad.rc   # missing khatam
if "$BIN" run /tmp/rc_bad.rc >/dev/null 2>&1; then echo "  FAIL: bad program should have errored"; fail=1; else echo "  PASS bad-program-errors"; fi

[ "$fail" -eq 0 ] && echo "ALL TESTS PASSED" || echo "SOME TESTS FAILED"
exit $fail
