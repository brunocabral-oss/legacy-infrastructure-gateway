# Security Policy

## 1. Principles

The **Legacy Infrastructure Gateway (LIG)** acts as a controlled boundary between consumers and critical network infrastructure. Security is fail-closed by default.

Key pillars:
- **Read-Only by Default**: No device configuration changes or write operations are allowed in the MVP.
- **No Arbitrary CLI Execution**: No open `exec` or raw shell commands are exposed to standard consumers.
- **Immutable Audit Logging**: Every interaction (allowed, denied, failed) is recorded with request ID, actor, source IP, device, and timing.
- **Zero Credentials Exposure**: Passwords, tokens, SSH keys, communities, and secrets must NEVER appear in logs, API responses, exceptions, or database tables.
- **Deny by Default**: Unknown operations, unknown devices, or unsupported capabilities are denied immediately.

## 2. Redaction & Data Protection

All log formatters and response serializers enforce redacting of sensitive patterns:
- Passwords (`password`, `secret`, `enable_secret`, `community`, `token`)
- Private keys (`BEGIN RSA PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY`, etc.)
- Session tokens and authorization headers

## 3. Reporting a Vulnerability

If you discover a security vulnerability in LIG, please do not file a public issue.
Report vulnerabilities confidentially to the security maintainers or open a private security advisory on GitHub.

Include:
- Type of vulnerability
- Steps to reproduce
- Potential impact
- Suggested remediation, if available
