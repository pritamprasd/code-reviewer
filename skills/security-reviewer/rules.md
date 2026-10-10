# Security Code Review Guidelines (OWASP Aligned)

When reviewing code under this skill, evaluate the diff against these critical security requirements:

## 1. Injection (SQL, Command, LDAP, NoSQL)
- **SQL / Query Injection**: Flag dynamic string interpolation or concatenation in database queries. Parameters must be strictly bound using prepared statements or ORM parameter binding.
- **Command Injection**: Flag `Runtime.getRuntime().exec()`, `subprocess.call(..., shell=True)`, or `child_process.exec()` where arguments contain unsanitized user inputs.
- **Path Traversal**: Flag constructing file paths using untrusted user input without canonicalization and directory restriction (`../` attacks).

## 2. Broken Authentication & Authorization
- **Missing Access Control**: Check that protected business operations verify user permissions, role, and tenant ownership.
- **Insecure Direct Object References (IDOR)**: Flag retrieving resources purely by user-supplied ID without verifying the requesting user owns that resource.
- **Insecure JWT / Token Handling**: Flag missing expiration checks, weak algorithms (e.g. `none`), or storing sensitive data in JWT payloads.

## 3. Cryptographic Failures & Sensitive Data
- **Hardcoded Secrets**: Flag hardcoded passwords, private keys, API keys, AWS credentials, or connection strings.
- **Weak Cryptography**: Flag deprecated algorithms (MD5, SHA1 for passwords, DES, ECB mode). Passwords must use Argon2id, bcrypt, or PBKDF2 with salt.
- **Data Exposure**: Flag logging sensitive fields (passwords, SSNs, credit cards, auth tokens).

## 4. Cross-Site Scripting (XSS) & Input Validation
- **Reflected / Stored XSS**: Flag rendering untrusted user input directly in HTML without escaping or sanitization.
- **Unvalidated Redirects**: Flag redirecting to user-controlled URLs without domain allowlisting.
