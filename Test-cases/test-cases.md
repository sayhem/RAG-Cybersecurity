# Cybersecurity RAG System — Test Queries and Results

This document presents 14 representative test cases used to evaluate the cybersecurity RAG system. Each test case includes the submitted query and the corresponding screenshot of the system's response.

## 1. Cybersecurity Questions

### 1

**Query:** What is broken access control?

**Observed result:**

![System response to the broken access control query](images/cyber-questions/test-01-broken-access-control.png)

### 2

**Query:** What is the difference between identification, authentication, and authorization in cybersecurity?

**Observed result:**

![System response explaining identification and authentication](images/cyber-questions/test-02-identity-access-management-part-1.png)

![Continuation of the system response explaining authorization and listing sources](images/cyber-questions/test-02-identity-access-management-part-2.png)

### 3

**Query:** What is SQL injection, how does it occur, and what security practices can reduce the risk?

**Observed result:**

![System response defining SQL injection and explaining how it occurs](images/cyber-questions/test-03-sql-injection-part-1.png)

![Continuation of the system response describing security practices](images/cyber-questions/test-03-sql-injection-part-2.png)

![Continuation of the system response listing sources](images/cyber-questions/test-03-sql-injection-part-3.png)

### 4

**Query:** Briefly explain credential dumping and how attackers can use stolen credentials after gaining access to a system.

**Observed result:**

![System response explaining credential dumping and the use of stolen credentials](images/cyber-questions/test-04-credential-dumping.png)

### 5

**Query:** Why do cryptographic failures happen?

**Observed result:**

![System response explaining the causes of cryptographic failures](images/cyber-questions/test-05-cryptographic-failures.png)

## 2. Cybersecurity Incident Scenarios

### 6

**Query:** A compromised endpoint accessed several large, sensitive files and then sent an unusually large amount of HTTPS traffic to a legitimate cloud-storage service. What attacker behavior may this represent, and what host and network evidence should investigators review?

**Observed result:**

![System response interpreting the behavior and describing host evidence](images/incident-descriptions/test-06-data-exfiltration-part-1.png)

![Continuation of the system response describing network evidence and listing sources](images/incident-descriptions/test-06-data-exfiltration-part-2.png)

### 7

**Query:** A remote service received hundreds of repeated password attempts against several employee accounts. One account was then accessed successfully using the correct password. What attack technique may this represent, and what authentication and login evidence should investigators review?

**Observed result:**

![System response interpreting the repeated password attempts and describing evidence to review](images/incident-descriptions/test-07-password-spraying.png)

### 8

**Query:** Security monitoring detected a process attempting to access LSASS memory on a compromised Windows endpoint. Shortly afterward, the same account was used to access another system. What attacker behavior may this represent?

**Observed result:**

![System response interpreting LSASS memory access followed by access to another system](images/incident-descriptions/test-08-lsass-credential-access.png)

### 9

**Query:** An incident has been contained, and the affected systems are ready to be restored. Briefly explain how recovery actions should be selected, performed, verified, and communicated.

**Observed result:**

![System response explaining incident recovery actions](images/incident-descriptions/test-09-incident-recovery.png)

### 10

**Query:** Security monitoring detected a newly created scheduled task that launches an unfamiliar executable whenever a user logs in. What attacker behavior could this indicate?

**Observed result:**

![System response interpreting the newly created scheduled task](images/incident-descriptions/test-10-scheduled-task-persistence.png)

## 3. Out-of-Scope Questions

These tests verify that the system appropriately rejects questions unrelated to cybersecurity.

### 11

**Query:** How is the weather today?

**Observed result:**

![System response to an unrelated weather question](images/unrelated-questions/test-11-weather-question.png)

### 12

**Query:** What is the capital of France?

**Observed result:**

![System response to an unrelated geography question](images/unrelated-questions/test-12-geography-question.png)

## 4. Failure Cases

These tests document cases in which the retrieved cybersecurity material did not provide sufficient information for the system to produce a complete answer.

### 13

**Query:** A public-facing web application started returning unusual database errors after receiving requests containing SQL syntax in URL parameters. Shortly afterward, sensitive customer records appeared to have been accessed. What vulnerability or attack could explain this activity, and what incident response steps should be considered?

**Observed result:**

![System response with insufficient information for the web application incident](images/failure-cases/test-13-insufficient-incident-response-context.png)

### 14

**Query:** What is OWASP 10?

**Observed result:**

![System response with insufficient information for the OWASP 10 query](images/failure-cases/test-14-insufficient-owasp-context.png)
