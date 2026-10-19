// Runs the real robot_chalao package (from the release wheel) in Pyodide.
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

let py = null;

async function boot(wheel) {
  py = await loadPyodide();
  await py.loadPackage(["micropip", "pyyaml"]);
  const micropip = py.pyimport("micropip");
  await micropip.install(new URL(wheel, self.location.href).href);
  py.runPython(`
import io, os, contextlib
from robot_chalao import cli, __version__
os.makedirs("/work", exist_ok=True)

def _run(argv, files):
    for name, text in files.items():
        with open("/work/" + name, "w") as f:
            f.write(text)
    os.chdir("/work")
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            rc = cli.main(argv)
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 1
    return rc, out.getvalue()
`);
  return py.globals.get("__version__");
}

self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.type === "boot") {
      const v = await boot(m.wheel);
      self.postMessage({ type: "ready", version: v });
    } else if (m.type === "run") {
      const run = py.globals.get("_run");
      const files = py.toPy({ "prog.rc": m.code, "chalao.yaml": m.config });
      const res = run(py.toPy(m.argv), files).toJs();
      self.postMessage({ type: "done", id: m.id, rc: res[0], out: res[1] });
    }
  } catch (err) {
    self.postMessage({ type: "error", id: m.id, message: String(err) });
  }
};
