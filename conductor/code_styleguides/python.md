# Google Python Style Guide Summary

This document summarizes key rules and best practices from the Google Python Style Guide for the backend of Resume Maker.

## 1. Python Language Rules
- **Linting:** Run linter/type checker on code to catch bugs.
- **Imports:** Use explicit imports. Standard library, third-party, and application imports should be grouped.
- **Exceptions:** Use built-in exception classes. Avoid bare `except:`.
- **Default Argument Values:** Do not use mutable objects as default values.
- **Type Annotations:** Required for FastAPI route handlers and service functions.

## 2. Python Style Rules
- **Indentation:** 4 spaces.
- **Docstrings:** Use docstrings for public modules, classes, and service functions.
- **Strings:** Use f-strings for string formatting.
- **Naming:** `snake_case` for functions/variables, `PascalCase` for Pydantic models & classes, `ALL_CAPS` for constants.
