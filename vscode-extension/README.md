# Robot Chalao — VS Code extension

Syntax highlighting, bracket matching, and snippets for the Robot Chalao Hinglish
robot language (`.rc` files).

## Features
- Keyword, robot-verb, type, string, number and comment highlighting.
- Auto-closing brackets and quotes, `#` line comments.
- Snippets: `agar`, `jabtak`, `har`, `kaam`, `koshish`, `timer`, `jodo`, `jaopose`,
  `seedha`, `aage`, `yahan`, `dhundo`, `sun`.

## Install (from source)
```bash
cd vscode-extension
npm install -g @vscode/vsce   # once
vsce package                  # makes robot-chalao-0.1.0.vsix
code --install-extension robot-chalao-0.1.0.vsix
```
Or copy this folder into `~/.vscode/extensions/robot-chalao/` and reload VS Code.

Open any `.rc` file and highlighting starts automatically.

## License
MIT.
