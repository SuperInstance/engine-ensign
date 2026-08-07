# Contributing to engine-ensign

## Development Setup

```bash
git clone https://github.com/SuperInstance/engine-ensign.git
cd engine-ensign
pip install -e ".[dev]"
```

## Running Tests

```bash
# Full suite
python -m pytest -v

# With coverage
python -m pytest --cov=tools --cov-report=term-missing

# Single file
python -m pytest tests/test_generate_config.py -v

# Single test class
python -m pytest tests/test_generate_config.py::TestSanitizeName -v
```

## Project Structure

```
tools/           Python tools (config generator, dashboard designer)
tests/           pytest test suite (156+ tests)
firmware/        ESP32 C firmware, one dir per engine config
dashboards/      JSON dashboard layout configs
agent/           Agent identity, memory, preferences, alert history
tripartite/      Pathos/Logos/Ethos decision framework
```

## Code Style

- Follow existing patterns in the codebase
- Every new feature needs test coverage
- Use conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`
- Python 3.10+ — use type hints on all function signatures
- Keep tools as pure functions where possible (easier to test)

## Adding a New Sensor Type

1. Add the sensor spec to `SENSOR_TYPES` in `tools/generate_config.py`
2. Add tests in `tests/test_generate_config.py`
3. Add edge-case tests in `tests/test_edge_cases.py`
4. Update the relevant firmware `sensors.h` if needed
5. Document in `agent/design_decisions.md`

## Adding a New Display Type

1. Add the display spec to `DISPLAYS` in `tools/generate_config.py`
2. Add parametrized tests (they auto-cover all displays via `@pytest.mark.parametrize`)
3. Create a dashboard JSON in `dashboards/` for the new resolution
4. Verify with `python tools/dashboard_designer.py --list`

## Pull Request Checklist

- [ ] Tests pass: `python -m pytest -v`
- [ ] New code has test coverage
- [ ] No secrets or credentials committed
- [ ] Documentation updated if behavior changed
- [ ] `pyproject.toml` version bumped if releasing

## Architecture

See [README.md](README.md) for the four-layer architecture (firmware, dashboards, agent, tripartite).
See [PHILOSOPHY.md](PHILOSOPHY.md) for the sickbay/holo-emitter design vision.
