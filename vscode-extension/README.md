# Robot Chalao — VS Code extension

Syntax highlighting, bracket matching, and snippets for the Robot Chalao Hinglish
robot language (`.rc` files).

## Features
- Keyword, robot-verb, type, string, number and comment highlighting.
- Auto-closing brackets and quotes, `#` line comments.
- Snippets: `agar`, `jabtak`, `har`, `kaam`, `koshish`, `timer`, `jodo`, `jaopose`,
  `seedha`, `aage`, `yahan`, `dhundo`, `sun`.
- Short aliases (`bas`, `bol`, `rakh`, `try`, `de`, `tod`) and scientific-notation numbers highlight like the full keywords.

## Install

Download `robot-chalao-<version>.vsix` from the [latest release](https://github.com/megazron/robot-chalao/releases/latest), then:

```bash
code --install-extension robot-chalao-1.0.0.vsix
```

## Build from source
```bash
cd vscode-extension
npm install -g @vscode/vsce   # once
vsce package                  # makes robot-chalao-1.0.0.vsix
code --install-extension robot-chalao-1.0.0.vsix
```
Or copy this folder into `~/.vscode/extensions/robot-chalao/` and reload VS Code.

Open any `.rc` file and highlighting starts automatically.

## License
MIT.
