# Changelog

## 0.1.0 (2025-11-17)


### Features

* achieve 100% e2e test success - all 31 routes working! ([fd65c9f](https://github.com/4thel00z/sdkgen/commit/fd65c9f2198885d585659f87411b74573794db20))
* add end-to-end test script with automated API testing ([ff64141](https://github.com/4thel00z/sdkgen/commit/ff64141950fbb884ce18107e36175774de18975c))
* add guardian pattern, reorganize docs, enforce linter best practices, fix mypy errors ([4ad7756](https://github.com/4thel00z/sdkgen/commit/4ad7756157e37a5a5dcb0de79c38b0549ea8f096))
* add professional Makefile, GitHub workflows, improve README, and publish to PyPI ([98b8569](https://github.com/4thel00z/sdkgen/commit/98b8569162c6c597d72ebc6b0acd7d0faf789680))
* add release-please for automated release management ([5bb319e](https://github.com/4thel00z/sdkgen/commit/5bb319e175be4758b15ad22f25173424ca692f2b))
* enhance endpoint analysis and IR builder ([a1b3e1c](https://github.com/4thel00z/sdkgen/commit/a1b3e1cfb840def2274f4af4a87496756c45d4e8))
* initial SDKGen implementation - OpenAPI to Python SDK generator ([2ef95b5](https://github.com/4thel00z/sdkgen/commit/2ef95b53f344f4886c74a38850eef6fb22fbf312))


### Bug Fixes

* add --system flag to uv pip install in CI ([f66b425](https://github.com/4thel00z/sdkgen/commit/f66b425337d5fcafad49030b9f7ce19ee6acd031))
* call tools directly after uv tool install ([796af0a](https://github.com/4thel00z/sdkgen/commit/796af0a32038e8e9c1e2082450eb8019c2b9726e))
* correct GitHub username and README list formatting ([c434962](https://github.com/4thel00z/sdkgen/commit/c434962e9aea70c954feda225726b35b798f0ba8))
* correct tool installation strategy in CI ([c94c94e](https://github.com/4thel00z/sdkgen/commit/c94c94efc385c3a88b82defd397a98451ca08ffc))
* improve array parameter naming and handle spaces in identifiers ([c77e39b](https://github.com/4thel00z/sdkgen/commit/c77e39b76e97d17b75c0734543471773e73440ed))
* include logo.png in package distribution ([01cd4c7](https://github.com/4thel00z/sdkgen/commit/01cd4c7603c77b67f2fb89fc157154c7ca3bffbd))
* remove resource name pluralization and namespace URL doubling ([f96e4ec](https://github.com/4thel00z/sdkgen/commit/f96e4ec93a2ca75a94f47ddbf92fff80030530ce))
* resolve CI type errors and test failures ([942d440](https://github.com/4thel00z/sdkgen/commit/942d440eb28e289e1037b47f5692746ccbc1813b))
* separate beta endpoints into individual resources ([2d38802](https://github.com/4thel00z/sdkgen/commit/2d388029a55cda2763875c494a1bb9e4dc0ac21a))
* update CI workflow to use uv sync and uv run ([ec9be74](https://github.com/4thel00z/sdkgen/commit/ec9be74148fe5a8d1d6b39c39750f14a6e8464e1))
* use --all-extras flag with uv sync to install dev dependencies ([3c45551](https://github.com/4thel00z/sdkgen/commit/3c45551406c09d9e96d07134a2223d56454e3721))
* use GitHub raw URL for logo to fix PyPI display ([298835c](https://github.com/4thel00z/sdkgen/commit/298835ce01128aba539c65e20fdc0180913122f3))
* use uv pip install for dev dependencies in CI ([917f72d](https://github.com/4thel00z/sdkgen/commit/917f72d100589365fa447d07275024e9afa55f53))
* use uv tool install for dev tools in CI ([43202b6](https://github.com/4thel00z/sdkgen/commit/43202b6082b9d5fe60a7160ff77dd42cddd53b97))


### Documentation

* add comprehensive session history and docstring plan ([b9bdb99](https://github.com/4thel00z/sdkgen/commit/b9bdb99b0ab32748902b2a29a24c6562d1a16e2d))
* add OpenAI-style docstrings to analyzers/ (endpoint, namespace, naming, nested) ([ce17293](https://github.com/4thel00z/sdkgen/commit/ce17293f7bf7177568f61f02657d7ae0621bc1f6))
* add OpenAI-style docstrings to core/ (parser, resolver, type_mapper) ([0d46eca](https://github.com/4thel00z/sdkgen/commit/0d46ecae0823bb3c4e475a1f228491630204c9e7))
* add OpenAI-style docstrings to core/ (schema_analyzer, partial ir_builder) ([e4aeed4](https://github.com/4thel00z/sdkgen/commit/e4aeed44f43d3cdb0ecb2aa4dfda767e6fa837fb))
* add OpenAI-style docstrings to utils/ (case_converter, name_sanitizer, http_cache) ([74bf231](https://github.com/4thel00z/sdkgen/commit/74bf23186aec5584870d5482f1c86447ef8a520c))
* add release-please usage guide to AGENT.md and cursorrules ([7aa040f](https://github.com/4thel00z/sdkgen/commit/7aa040ff51dc9c7dba7c31a65f5d962dff3c18e1))
* update README.md ([2376a84](https://github.com/4thel00z/sdkgen/commit/2376a84f8d653fd9f7c7aaa556a07ff1784f2508))

## [0.2.0](https://github.com/4thel00z/sdkgen/compare/v0.1.3...v0.2.0) (2025-11-16)

### Features

* achieve 100% e2e test success - all 31 routes working! ([fd65c9f](https://github.com/4thel00z/sdkgen/commit/fd65c9f))
* add end-to-end test script with automated API testing ([ff64141](https://github.com/4thel00z/sdkgen/commit/ff64141))
* add guardian pattern and enforce linter best practices ([4ad7756](https://github.com/4thel00z/sdkgen/commit/4ad7756))
* add professional Makefile, GitHub workflows, improve README ([98b8569](https://github.com/4thel00z/sdkgen/commit/98b8569))

### Bug Fixes

* remove resource name pluralization and namespace URL doubling ([f96e4ec](https://github.com/4thel00z/sdkgen/commit/f96e4ec))
* separate beta endpoints into individual resources ([2d38802](https://github.com/4thel00z/sdkgen/commit/2d38802))
* improve array parameter naming and handle spaces in identifiers ([c77e39b](https://github.com/4thel00z/sdkgen/commit/c77e39b))
* resolve CI type errors and test failures ([942d440](https://github.com/4thel00z/sdkgen/commit/942d440))
* correct tool installation strategy in CI ([c94c94e](https://github.com/4thel00z/sdkgen/commit/c94c94e))

## [0.1.3](https://github.com/4thel00z/sdkgen/compare/v0.1.2...v0.1.3) (2025-11-16)

### Bug Fixes

* correct GitHub username and README list formatting ([c434962](https://github.com/4thel00z/sdkgen/commit/c434962))
* use GitHub raw URL for logo to fix PyPI display ([298835c](https://github.com/4thel00z/sdkgen/commit/298835c))

## [0.1.2](https://github.com/4thel00z/sdkgen/compare/v0.1.1...v0.1.2) (2025-11-16)

### Bug Fixes

* use GitHub raw URL for logo to fix PyPI display

## [0.1.1](https://github.com/4thel00z/sdkgen/compare/v0.1.0...v0.1.1) (2025-11-16)

### Bug Fixes

* include logo.png in package distribution

## 0.1.0 (2025-11-16)

### Features

* Initial release
* Multi-language SDK generator from OpenAPI specifications
* Complete OpenAPI 3.x support
* Python SDK generation with async-first pattern
* Type-safe TypedDict models
* Intelligent method naming (3-priority system)
* Namespace support for API versioning
