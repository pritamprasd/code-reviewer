# Clean Code & Architectural Guidelines

When reviewing code under this skill, evaluate the diff against these universal software engineering principles:

## 1. SOLID & Object-Oriented Principles
- **Single Responsibility Principle (SRP)**: Flag classes or functions doing more than one distinct task.
- **Open/Closed Principle**: Flag massive switch/if-else chains checking types; suggest polymorphism, strategy patterns, or dictionary dispatch.
- **Interface Segregation**: Flag bloated interfaces forcing classes to implement dummy methods.
- **Dependency Inversion**: Flag high-level modules directly instantiating low-level concrete implementations (`new ConcreteService()`).

## 2. Error Handling & Defensive Programming
- **Empty Catch Blocks**: Flag catching exceptions without logging, rethrowing, or handling.
- **Catching Generic `Exception` or `Throwable`**: Enforce catching specific, meaningful exceptions.
- **Resource Leaks**: Ensure files, streams, database connections, and sockets use `try-with-resources` (Java) or context managers (`with` in Python) or explicit cleanup.
- **Null Safety**: Flag missing null checks on nullable return values.

## 3. Naming & Readability
- **Meaningful Names**: Flag ambiguous single-letter variables (e.g. `d`, `temp`, `data2`) unless in standard loop counters.
- **Magic Numbers & Strings**: Flag hardcoded numbers or strings without named constants.
- **Function Length & Complexity**: Flag functions exceeding ~40 lines or cyclomatic complexity > 8.

## 4. Concurrency & Performance
- **Premature / Inefficient Operations**: Flag unnecessary repeated database queries in loops, expensive serialization inside critical paths, or unbounded collections.
- **Thread Safety**: Flag race conditions, unsynchronized mutations of shared mutable state.
