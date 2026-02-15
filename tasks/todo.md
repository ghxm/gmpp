# gmpp Implementation

## Phase 1: Core framework
- [x] pyproject.toml (hatchling, optional extras, entry point)
- [x] document.py (Document dataclass, StepRecord NamedTuple)
- [x] registry.py (component + metric registries, decorators, factory)
- [x] component.py (Component ABC, get_params/set_params, to_dict/from_dict)
- [x] pipeline.py (Pipeline, run/run_corpus, config serialization)
- [x] __init__.py (public API exports)

## Phase 2: Evaluation
- [x] eval.py (5 metrics: rouge_lsum, levenshtein, token_precision/recall/f1)
- [x] evaluate() and evaluate_corpus() functions

## Phase 3: I/O and CLI
- [x] io.py (load_corpus, save_results, load_results, save_eval)
- [x] cli.py (gmpp run/eval/list/show/inspect)

## Phase 4: Components
- [x] components/trafilatura.py
- [x] components/readability.py
- [x] components/justext.py
- [x] components/newspaper.py
- [x] components/inscriptis.py
- [x] components/__init__.py (auto-import with silent ImportError)

## Phase 5: Documentation
- [x] README.md
- [x] CONTRIBUTING.md
- [x] mkdocs.yml + docs/ site (12 pages)

## Tests
- [x] conftest.py (fixtures + UpperCaseComponent)
- [x] test_document.py (7 tests)
- [x] test_component.py (6 tests)
- [x] test_pipeline.py (8 tests)
- [x] test_registry.py (7 tests)
- [x] test_eval.py (27 tests)
- [x] test_io.py (11 tests)
- [x] test_cli.py (14 tests)

## Integration verification
- [x] All 80 tests passing
- [x] `gmpp list` shows all 5 components + 5 metrics
- [x] Package installs cleanly via uv

## Bug fixes during implementation
- get_params() was picking up *args/**kwargs from object.__init__ for components
  without custom __init__; fixed by filtering VAR_POSITIONAL/VAR_KEYWORD params
