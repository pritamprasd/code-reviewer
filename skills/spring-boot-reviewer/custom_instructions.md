# Spring Boot Custom Team Instructions

- **DTO Design**: Enforce Java 17+ records for request/response DTOs rather than mutable classes where feasible.
- **Mapping**: Recommend MapStruct over manual builder or reflection-based ModelMapper.
- **Transactions**: Strictly check that private methods are NOT annotated with `@Transactional`. Check that transactions are not held during external REST/Kafka calls.
- **Logging**: Ensure SLF4J is used via `@Slf4j` (Lombok) and never use `System.out.println`.
