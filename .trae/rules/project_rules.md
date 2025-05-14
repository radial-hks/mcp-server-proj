# mcp-server-proj 项目规则

本文档旨在为 `mcp-server-proj` 项目的开发和维护提供一套指导规则，以确保代码质量、一致性和可维护性。

## 1. 代码风格

- **格式化:** 强制使用 `black` 进行代码格式化。在提交代码前运行 `black .`。
- **Linting:** 使用 `ruff` 或 `flake8` 进行代码质量检查。配置应包含在 `pyproject.toml` 中。
- **命名规范:** 遵循 PEP 8 命名规范。
  - 模块名：`lowercase_with_underscores`
  - 类名：`CapWords`
  - 函数/方法名：`lowercase_with_underscores`
  - 变量名：`lowercase_with_underscores`
  - 常量名：`ALL_CAPS_WITH_UNDERSCORES`
- **类型提示:** 强烈建议使用类型提示 (Type Hinting)，并使用 `mypy` 进行静态类型检查。

## 2. 项目结构

- **源代码:** 所有项目源代码应位于 `src/mcp_server_proj/` 目录下。
- **测试代码:** 所有测试代码应位于顶层的 `tests/` 目录下，并遵循与 `src/` 相似的结构。
- **模块化:** 保持模块的高内聚、低耦合。核心功能应封装在 `core` 包中。
- **配置文件:** 项目配置（如 `pyproject.toml`）应位于项目根目录。

## 3. 依赖管理

- **声明:** 所有项目依赖项必须在 `pyproject.toml` 的 `[project.dependencies]` 部分声明。
- **开发依赖:** 开发、测试和构建依赖项应在 `pyproject.toml` 的 `[project.optional-dependencies]` 中声明（例如，`dev`, `test`）。
- **锁定:** 使用 `uv lock` 或类似工具生成并维护 `uv.lock` 文件，以确保可复现的构建环境。
- **环境管理:** 推荐使用 `uv` 创建独立的虚拟环境。

## 4. 异步编程 (Asyncio)

- **一致性:** 在 I/O 密集型操作（如网络请求、文件读写）中优先使用 `async`/`await`。
- **库选择:** 优先选择支持 `asyncio` 的库（如 `aiohttp`, `asyncpg`）。
- **阻塞调用:** 避免在异步函数中直接调用阻塞的同步代码。如果必须调用，请使用 `asyncio.to_thread`。
- **入口点:** 使用 `asyncio.run()` 作为主程序的入口点，如 `src/mcp_server_proj/__init__.py` 中所示。

## 5. 测试

- **框架:** 使用 `pytest` 作为测试框架。
- **覆盖率:** 目标是实现高测试覆盖率。使用 `pytest-cov` 插件进行测量。
- **测试类型:** 编写单元测试、集成测试和（如果适用）端到端测试。
- **测试发现:** 测试文件应以 `test_` 开头或以 `_test` 结尾。测试函数应以 `test_` 开头。

## 6. 文档

- **Docstrings:** 为所有公共模块、类、函数和方法编写清晰的 Docstrings。推荐使用 Google 或 NumPy 风格。
- **README:** 保持 `README.md` 文件更新，包含项目概述、安装指南、使用示例和配置说明。
- **注释:** 对复杂或不直观的代码段添加必要的行内注释。

## 7. 版本控制 (Git)

- **提交信息:** 遵循 Conventional Commits 规范编写提交信息。
- **分支策略:** 使用 Gitflow 或类似的特性分支工作流。
- **代码审查:** 所有代码变更在合并到主分支（如 `main` 或 `master`）之前必须经过代码审查。
- **`.gitignore`:** 维护 `.gitignore` 文件，排除不必要的文件（如 `__pycache__`, `*.pyc`, 虚拟环境目录, IDE 配置等）。
