# Contributing to Downloads Cleanup Manager

First off, thank you for considering contributing to the Downloads Cleanup Manager! The whole point of this project was to solve a problem I had with managing my downloads using my Ubuntu Linux, so I hope it'll be of help to you and you can make it even better for others.

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally.
3. **Set up the environment**: We'll use `conda` to manage our dependencies.
   ```bash
   conda env create -f environment.yml
   conda activate downloads_cleanup
   ```
4. **Create a `.env` file** and configure your `config/config.json` as described in the Configuration documentation.

## Architecture Guidelines

This project strictly follows **Domain-Driven Design (DDD)**. Before adding a new feature, please familiarize yourself with the architectural layers:

- `src/domain/`: Pure Python. No external dependencies. Models, Rules, and Policies go here.
- `src/application/`: Orchestrates the domain. Defines interfaces (Ports).
- `src/infrastructure/`: Concrete implementations (Adapters) for file systems, config parsers, and APIs.

*Note: The Domain layer must never import from the Application or Infrastructure layers.*

## Testing

We use `pytest`. You must ensure that your code is covered by unit tests and that all existing tests pass before submitting a Pull Request.

To run the test suite:
```bash
pytest -v tests/
```

We also enforce a security audit via `bandit` in our CI pipelines. You can run it locally:
```bash
bandit -r src/ -ll
```

## Pull Request Process

1. Ensure any new features are thoroughly tested.
2. Update the `docs/` folder if you change configuration files, architecture, or behavior.
3. Ensure your PR description clearly describes the problem and solution.
4. Once you submit a PR, our GitHub Actions CI will run your code against `pytest` and `bandit`. Both must pass before your code can be reviewed.
