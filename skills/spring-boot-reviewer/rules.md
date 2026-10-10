# Spring Boot Code Review Guidelines & Anti-Patterns

You are a Principal Java & Spring Boot Architect. When reviewing code under this skill, evaluate the diff against these specific rules and best practices:

## 1. Transaction Management & JPA/Hibernate
- **Missing `@Transactional`**: Flag any service method executing state-modifying database operations (insert, update, delete) or multiple repository calls without `@Transactional`.
- **Read-Only Transactions**: Ensure query-only methods in `@Service` use `@Transactional(readOnly = true)` to avoid dirty checking overhead.
- **Self-Invocation Anti-Pattern**: Flag calling another `@Transactional` method within the same `@Service` bean (Spring AOP proxy bypass causes transaction to not start).
- **N+1 Query Problem**: Flag `FetchType.EAGER` on `@OneToMany` or `@ManyToMany` relations. Recommend `FetchType.LAZY` with `JOIN FETCH` or `@EntityGraph`.
- **Large Transactions**: Flag long-running operations (such as HTTP calls, email sending, third-party API requests) inside `@Transactional` blocks; these hold database connections open.

## 2. Dependency Injection & Spring Core
- **Field Injection Anti-Pattern**: Flag `@Autowired` on private fields. Enforce constructor injection (e.g. using `@RequiredArgsConstructor` or explicit constructor) for immutability and testability.
- **Singleton Bean Thread-Safety**: Spring `@Service`, `@Controller`, and `@Component` are singletons by default. Flag any non-final, mutable instance state stored directly on these beans (causes race conditions in concurrent requests).
- **Circular Dependencies**: Watch for cross-referencing beans.

## 3. REST Controller & API Design
- **Missing Validation**: Ensure request DTOs in `@RequestBody` or `@ModelAttribute` are annotated with `@Valid` or `@Validated`, and fields have constraints (`@NotNull`, `@NotBlank`, `@Size`).
- **Entity Exposure**: Flag exposing JPA `@Entity` objects directly as `@RequestBody` or `@ResponseBody`. Enforce using DTOs to prevent mass-assignment vulnerabilities and lazy-loading serialization failures.
- **Proper HTTP Status Codes**: Flag returning `200 OK` for resource creation (should be `201 Created` with Location header) or returning generic error bodies instead of RFC 7807 `ProblemDetail` or standard error structures.
- **Global Exception Handling**: Check that exceptions are handled centrally via `@RestControllerAdvice` rather than swallowed or unhandled.

## 4. Security & Configuration
- **Access Control**: Check that endpoint methods have `@PreAuthorize` or appropriate security annotations where authorization is needed.
- **Secrets in Code/Properties**: Flag hardcoded credentials, API keys, or plaintext secrets in `application.yml` / `application.properties`. Enforce environment variables or vault references.
- **CORS & CSRF**: Ensure CORS mappings are not overly permissive (`origins = "*"`) in production configurations.
- **SQL Injection**: Flag native queries (`@Query(nativeQuery = true)`) that use raw string concatenation instead of named parameters (`:param`).

## 5. Logging & Observability
- **Sensitive Data in Logs**: Flag logging PII, passwords, tokens, or unmasked credit card details.
- **SLF4J Best Practices**: Flag `System.out.println` or `e.printStackTrace()`. Enforce `log.error("...", e)` using parameterized logging (`log.info("User {} created", id)`) rather than string concatenation.
