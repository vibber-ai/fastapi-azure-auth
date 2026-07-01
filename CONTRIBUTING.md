# Contributing

This package is open to contributions 👏

To contribute, please follow these steps:

1. Create an issue explaining what you'd like to fix or add. This way, we can approve and discuss the
   solution before any time is spent on developing it.
2. Fork the upstream repository into a personal account.
3. Install [uv](https://docs.astral.sh/uv/), and install all dependencies using `uv sync`
4. [Optional] Activate the environment by running `source .venv/bin/activate`
5. Install [pre-commit](https://pre-commit.com/) (for project linting) by running `uv run pre-commit install`
6. Create a new branch for your changes.
7. Create and run tests with full coverage by running `uv run pytest --cov fastapi_azure_auth --cov-report=term-missing`
8. Push the topic branch to your personal fork.
9. Run `uv run pre-commit run --all-files` locally to ensure proper linting.
10. Create a pull request to the upstream repository with a detailed summary of your changes and what motivated the change.

If you need a more detailed walk through, please see this
[issue comment](https://github.com/vibber-ai/fastapi-azure-auth/issues/49#issuecomment-1056962282).
