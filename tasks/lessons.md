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
