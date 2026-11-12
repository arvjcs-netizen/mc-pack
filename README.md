# My 1.8.9 Resource Pack

Starter project for a Minecraft Java 1.8.9 resource pack, set up for VS Code + Claude Code.

## Setup
```bash
pip install -r requirements.txt
python build.py --install
```
Then in Minecraft: Options → Resource Packs → enable **MyPack**. Press **F3+T** to reload after changes.

## Using Claude Code
Open this folder in VS Code and start Claude Code. It will read `CLAUDE.md` for the
1.8.9 file conventions. Try prompts like:
- "Make a 16x16 PvP-style diamond sword texture and install the pack"
- "Write tools/gen_ores.py that generates all the ore textures in a pastel style"
- "Make the hotbar in widgets.png cleaner and more minimal"
