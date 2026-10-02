# Plugin validation — 2026-10-02

Codex CLI 0.158.0, Windows, Python 3.14.3.

| Check | Result |
|---|---|
| Review pipeline unit/CLI/provenance/fixture tests | 41 passed, 7.723 seconds |
| Plugin package/manifests/paths/archive tests | 4 passed, 0.501 seconds |
| Bundled Skill quick_validate | Skill is valid |
| Portable/compatibility identity and presentation | Match |
| Repository marketplace source resolution | ./academic-paper-reviewer within repo root |
| Offline plugin validator | PASS |
| Actual Codex marketplace add | marketplaceName=sunzus, alreadyAdded=false |
| Actual Codex plugin install | pluginId=academic-paper-reviewer@sunzus, version=0.2.0 |
| Actual Codex plugin list | installed=true, enabled=true |

The actual installed bundle is in Codex's normal managed cache. No manual copying
into the cache or edits to plugin enablement configuration were used. The CLI
performs registration and installation. No external MCP connection or authentication
was required by the skills-only package.

Review pipeline tests and the example review remain available under
`skills/academic-paper-reviewer`. Fixture judgments were authored by Codex and retained
as regressions; neither these tests nor package tests evaluate generalization to
unseen papers. Desktop UI rendering and a fresh live-model paper review are not part
of this validation. If the open app has cached its plugin list, reopen it and start a
new chat to load the plugin.

Run from the plugin root:

```powershell
python -m unittest discover -s skills/academic-paper-reviewer/tests -v
python -m unittest discover -s tests -v
python scripts/build_plugin.py --marketplace ../.agents/plugins/marketplace.json --marketplace-root ..
codex plugin list --marketplace sunzus --json
```
