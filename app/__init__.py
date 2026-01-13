import warnings

# Reduce noisy third-party deprecation warnings that arise from
# upstream libraries still using `datetime.utcnow()` or the legacy
# `crypt` module. These are safe to silence for now to keep test output
# focused on actionable issues.
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*crypt is deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*datetime.datetime.utcnow.*")
# Silence known upstream warnings from SQLAlchemy and python-jose
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"sqlalchemy.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"jose.*")
# passlib warning suppression removed — using argon2 now
