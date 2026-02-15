# Lessons Learned

## get_params() and inspect.signature
When using `inspect.signature(self.__init__)` to introspect constructor params
(scikit-learn style), filter out `VAR_POSITIONAL` and `VAR_KEYWORD` parameter
kinds. Otherwise, classes without a custom `__init__` will pick up `*args` and
`**kwargs` from `object.__init__`, causing `from_dict` round-trip failures.

## pyenv version issues
The parent directory `/Users/maxhaag/dev/.python-version` sets pyenv to 3.8.13
which is not installed. Use `PYENV_VERSION=3.13.0` or use `uv run` to avoid
this. The project venv uses Python 3.12.

## from __future__ import annotations and forward references
When removing `from __future__ import annotations` (unnecessary for Python 3.12+),
self-referential return types like `def from_dict(cls, ...) -> Document` in a class
body fail at runtime. Use string annotations: `-> "Document"`. Also, types imported
under `TYPE_CHECKING` must use string annotations if referenced in runtime signatures.

## pstdev vs stdev
`statistics.pstdev` is population std, `statistics.stdev` is sample std. For
evaluation corpora (samples from a larger population), use `stdev`.

## Document.__post_init__ content={} bug
`if not self.content` treats `{}` as falsy, so explicitly passing `content={}`
to `Document()` gets overwritten with `dict(self.input)`. This breaks the
`from_dict` round-trip when serialized content is empty. Needs a sentinel or
explicit `None` check instead.

## Silent ImportError swallowing in components/__init__.py
Catching bare `ImportError` on `importlib.import_module()` swallows both
"library not installed" (intended) and "bug in component code" (unintended).
Log or differentiate.
